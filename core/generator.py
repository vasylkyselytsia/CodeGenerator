import os

from django.core.files import File
from django.db.models import Case, When

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import get_formatter_by_name

from core.utils import InMemoryZip
from .models import Function, Keyword


class CodeGenerator(object):

    BASIC_METHODS = ["__assign__",   # =
                     "__add__",      # +
                     "__iadd__",     # +=
                     "__sub__",      # -
                     "__isub__",     # -=
                     "__mul__",      # *
                     "__imul__",     # *=
                     "__truediv__",  # /
                     "__idiv__",     # /=
                     "__lt__",       # <
                     "__le__",       # <=
                     "__gt__",       # >
                     "__ge__",       # >=
                     "__ne__",       # !=
                     "__eq__",       # ==
                     "__pr_a__",     # Prefix++
                     "__pf_a__",     # ++Postfix
                     "__pr_s__",     # Prefix--
                     "__pf_s__"      # --Postfix
                     ]
    METHOD_ORDERING = Case(*[When(value=value, then=pos) for pos, value in enumerate(BASIC_METHODS)])

    INDENTS = {
        "Python": 4,
        "C++": 2,
        "Java": 2,
        "C#": 2
    }
    LEXERS = {
        "Python": get_lexer_by_name("python", stripall=True),
        "C++": get_lexer_by_name("c++", stripall=True),
        "C#": get_lexer_by_name("c#", stripall=True),
        "Java": get_lexer_by_name("java", stripall=True)
    }
    GENERATORS = {
        "Python": "generate_python_code",
        "C++": "generate_cpp_code",
        "C#": "generate_csharp_code",
        "Java": "generate_java_code"
    }
    FORMATTER = get_formatter_by_name("html", linenos=True)
    STYLES = "<style>{}</style>".format(FORMATTER.get_style_defs('.highlight'))

    @classmethod
    def null_assertion(cls, obj):
        assert obj is not None, "Object is Null"

    def __init__(self, code_template):
        self.code_template = code_template
        self.INDENT = self.INDENTS.get(code_template.language.name, 2)
        self.language = code_template.language
        self.keywords = dict(Keyword.objects.filter(language=self.language).values_list("value", "template"))
        self.functions = dict(Function.objects.filter(language=self.language).values_list("value", "template"))
        self.class_name = self.code_template.name
        self.basic_functions = Function.objects.filter(
            language=self.language, value__in=["__init__", "__del__"]).order_by(
            Case(*[When(value=value, then=pos) for pos, value in enumerate(["__init__", "__del__"])]))

    def generate_basic_functions(self):
        functions = Function.objects.filter(language=self.language, value__in=self.BASIC_METHODS).order_by(
            self.METHOD_ORDERING)
        code = []
        for idx, f in enumerate(functions):
            func = f.template
            func = "\n".join(map(lambda x: (" " * self.INDENT) + x, func.split("\n")))
            code.append(func + "\n")

        return "\n".join(code) + "\n{another_methods}\n"

    def generate_base(self, name):
        base = Keyword.objects.filter(value='__class__', language=self.language).first()
        self.null_assertion(base)
        return str(base.template) % dict(name=name, code="{code}", variables="{variables}")

    def generate_python_code(self):

        def get_basic():
            func_s = []
            for f in self.basic_functions:
                if f.value == "__init__":
                    init = f.template.split("\n")
                    init.extend(["{0}self.{1} = kwargs.get('{1}', {2})".format(
                        " " * self.INDENT, x.name,
                        (x.default or "None") if x.v_type != "str" else "'%s'" % (x.default or "None"))
                        for x in self.code_template.add_ones.all()])
                    func_s.extend(map(lambda x: (" " * self.INDENT) + x, init))
                else:
                    func_s.extend(map(lambda x: (" " * self.INDENT) + x,  f.template.split("\n")))

            return "\n" + "\n\n".join(func_s) + "\n\n"

        def add_custom_funcs():
            result = []
            for func in self.code_template.add_ones_func.all():
                result.append(self.keywords["__function__"] % {"name": func.name})

            return "\n\n".join(("\n".join(map(lambda x: (" " * self.INDENT) + x, f.split("\n")))
                                for f in result))

        template = self.generate_base(self.class_name)

        template = template.format(code=get_basic() + self.generate_basic_functions())
        template = template.format(another_methods=add_custom_funcs())
        return [{"content": template, "name": "%s.py" % self.class_name}]

    def _generate_cpp_code(self, cppVersion="", body=";"):

        def get_variables():
            variables = "\n"
            for v in self.code_template.add_ones.all():
                tpl = "{} {};".format(self.keywords.get(v.v_type, v.v_type), v.name)
                variables += ((' ' * self.INDENTS[self.language.name]) + tpl + "\n")
            return variables

        def get_includes():
            if cppVersion:
                return '#include "{}.h"\n\n'.format(self.class_name)

            includes = ["iostream", "iomanip", "string"]
            includes = "\n".join(["#include <{}>".format(x) for x in includes])
            includes += "\n\nusing namespace std;\n\n"
            includes = "#ifndef {name}_H\n#define {name}_H\n\n".format(name=self.class_name) + includes
            return includes

        def get_basic_part():
            func_s = ["  public:\n" if not cppVersion else ""]
            for f in self.basic_functions:
                if f.value == "__init__":
                    func_s.append(f.template % {"class_name": self.class_name, "cppVersion": cppVersion,
                                                "body": " {\n\n  }" if cppVersion else body, "params": ""})
                    func_s.append(f.template % {
                        "class_name": self.class_name, "cppVersion": cppVersion,
                        "body": " {\n\n  }" if cppVersion else body,
                        "params": "const {}& object".format(self.class_name)})
                    func_s.append(f.template % {
                        "class_name": self.class_name, "cppVersion": cppVersion,
                        "body": "{\n%s\n  }" % ("\n".join(["{0}this->{1}={1};".format(
                            " " * (self.INDENT * 2),  v.name
                        ) for v in self.code_template.add_ones.all()])) if cppVersion else body,
                        "params": ", ".join(("{} {}".format(self.keywords.get(v.v_type, v.v_type), v.name)
                                             for v in self.code_template.add_ones.all()))})
                else:
                    func_s.append(f.template % {"class_name": self.class_name, "cppVersion": cppVersion, "body": body})
            return "\n{}".format(" " * self.INDENT).join(func_s) + "\n\n"

        def get_getter_and_setters():
            result = []
            templates = dict(Function.objects.filter(
                language=self.language, value__in=["__getattr__", "__setattr__"]).values_list("value", "template"))
            for var in self.code_template.add_ones.all():
                get_ter = templates["__getattr__"] % {
                    "variable_type": self.keywords.get(var.v_type, var.v_type),
                    "cppVersion": cppVersion,
                    "body": body if not cppVersion else "{{\n%s\n}}" % "{}return {};".format(
                        " " * self.INDENT * 2, var.name),
                    "variable_cap": var.name.lower().capitalize()
                }
                set_ter = templates["__setattr__"] % {
                    "variable_type": self.keywords.get(var.v_type, var.v_type),
                    "cppVersion": cppVersion,
                    "body": body if not cppVersion else "{{\n%s\n}}" % "{0}this->{1} = {1};".format(
                        " " * self.INDENT * 2, var.name),
                    "variable_cap": var.name.lower().capitalize(),
                    "variable": var.name
                }
                result.extend([get_ter, set_ter])
            if not result:
                return ""
            indent = " " * self.INDENT
            return "\n" + indent + "\n\n{}".format(indent).join(result)

        def add_custom_functions():
            result = []
            for func in self.code_template.add_ones_func.all():
                result.append(self.keywords["__function__"] % {
                    "f_type": self.keywords.get(func.f_type, func.f_type),
                    "name": func.name,
                    "cppVersion": cppVersion, "body": body
                })
            if not result:
                return ""
            indent = " " * self.INDENT
            return "\n" + indent + "\n\n{}".format(indent).join(result)

        template = get_includes() + (self.generate_base(self.class_name) if not cppVersion else "\n{code}")
        template = template.replace("{variables}", "%(variables)s")
        template = template.replace("{code}", "%(code)s")
        basic_func = self.generate_basic_functions()
        basic_func %= {"class_name": self.class_name, "body": body, "cppVersion": cppVersion}
        basic_func = get_basic_part() + basic_func.format(another_methods=get_getter_and_setters())
        basic_func += add_custom_functions()

        template %= {"code": basic_func, "variables": get_variables()}
        template = template + ("\n\n#endif // {}_H".format(self.class_name) if not cppVersion else "\n")
        return template.replace("{{", "{").replace("}}", "}")

    def generate_cpp_code(self):
        main = """
#include <iostream>
#include "%(class_name)s.h"

using namespace std;

int main(){
   std::cout << "Hello World" << std::endl; 
   %(class_name)s *instance = new %(class_name)s();
   return 0;
}
""" % {"class_name": self.class_name}
        return [
            {"name": "main.cpp", "content": main},
            {"name": "{}.h".format(self.class_name), "content": self._generate_cpp_code()},
            {"name": "{}.cpp".format(self.class_name), "content": self._generate_cpp_code(
                cppVersion="{}::".format(self.class_name), body="{{\n%s return; \n}}" % (" " * (self.INDENT * 2)))}
        ]

    def generate_csharp_code(self):

        def get_variables():
            variables = "\n"
            for v in self.code_template.add_ones.all():
                tpl = "public {} {} {{ get; set; }}".format(self.keywords.get(v.v_type, v.v_type), v.name)
                variables += ((' ' * self.INDENTS[self.language.name]) + tpl + "\n")
            return variables + "\n"

        def get_basic():
            func_s = []
            for f in self.basic_functions:
                if f.value == "__init__":
                    code = ["{0}{1} = {2};".format(" " * self.INDENT * 2, x.name, x.name.lower())
                            for x in self.code_template.add_ones.all()]
                    params = ", ".join(("{} {}".format(self.keywords.get(v.v_type, v.v_type), v.name.lower())
                                        for v in self.code_template.add_ones.all()))

                    func_s.append(f.template % {"class_name": self.class_name, "params": params,
                                                "code": "\n".join(code)})
                else:
                    func_s.append(f.template % {"class_name": self.class_name})

            return "\n" + "\n".join(func_s) + "\n"

        def add_custom_functions():
            result = []
            for func in self.code_template.add_ones_func.all():
                result.append(self.keywords["__function__"] % {
                    "f_type": self.keywords.get(func.f_type, func.f_type),
                    "name": func.name
                })
            if not result:
                return ""
            indent = " " * self.INDENT
            return "\n" + indent + "\n\n{}".format(indent).join(result)

        template = self.generate_base(self.class_name)
        template = template.replace("{code}", "%(code)s") % dict(
            code=get_basic() + get_variables() + self.generate_basic_functions()
        )
        template = template.replace("{another_methods}", "%(another_methods)s")
        template %= {"class_name": self.class_name, "another_methods": add_custom_functions()}
        template = template.replace("{{", "{").replace("}}", "}")
        return [{"name": "%s.cs" % self.class_name, "content": template}]

    def generate_java_code(self):

        def get_variables():
            variables = "\n"
            for v in self.code_template.add_ones.all():
                tpl = "private {} {};".format(self.keywords.get(v.v_type, v.v_type), v.name)
                variables += ((' ' * self.INDENTS[self.language.name]) + tpl + "\n")
            return variables + "\n"

        def get_basic():
            f = self.basic_functions.filter(value='__init__').get()
            code = ["{0}{1} = {2};".format(" " * self.INDENT * 2, x.name, x.name.lower())
                    for x in self.code_template.add_ones.all().order_by("-id")]
            params = ", ".join(("{} {}".format(self.keywords.get(v.v_type, v.v_type), v.name.lower())
                                for v in self.code_template.add_ones.all().order_by("-id")))

            return "\n" + f.template % {"class_name": self.class_name, "params": params,
                                        "code": "\n".join(code)} + "\n"

        def add_custom_functions():
            result = []
            for func in self.code_template.add_ones_func.all():
                result.append(self.keywords["__function__"] % {
                    "f_type": self.keywords.get(func.f_type, func.f_type),
                    "name": func.name
                })
            if not result:
                return ""
            indent = " " * self.INDENT
            return "\n" + indent + "\n\n{}".format(indent).join(result)

        def get_getter_and_setters():
            result = []
            templates = dict(Function.objects.filter(
                language=self.language, value__in=["__getattr__", "__setattr__"]).values_list("value", "template"))
            for var in self.code_template.add_ones.all():
                get_ter = templates["__getattr__"] % {
                    "variable_type": self.keywords.get(var.v_type, var.v_type),
                    "variable_cap": var.name.lower().capitalize(),
                    "variable": var.name
                }
                set_ter = templates["__setattr__"] % {
                    "variable_type": self.keywords.get(var.v_type, var.v_type),
                    "variable_cap": var.name.lower().capitalize(),
                    "variable": var.name
                }
                result.extend([get_ter, set_ter])
            if not result:
                return ""
            indent = " " * self.INDENT
            return "\n" + indent + "\n\n{}".format(indent).join(result)

        def add_main():
            params = ", ".join(("%s" % (v.default or 'null') if not v.v_type.lower().startswith("str")
                                else '"%s"' % (v.default or 'String')
                                for v in self.code_template.add_ones.all().order_by("-id")))
            main = """

  public static void main(String []args) {
    %(class)s my%(class_cap)s = new %(class)s(%(params)s);
  }

"""
            return main % {"class": self.class_name, "params": params,
                           "class_cap": self.class_name.lower().capitalize()}

        template = self.generate_base(self.class_name)
        template = template.replace("{code}", "%(code)s") % dict(
            code=get_basic() + get_variables() + get_getter_and_setters() + self.generate_basic_functions()
        )
        template = template.replace("{another_methods}", "%(another_methods)s")
        template %= {"class_name": self.class_name, "another_methods": add_custom_functions() + add_main()}
        template = template.replace("{{", "{").replace("}}", "}")
        return [{"name": "%s.java" % self.class_name, "content": template}]

    def generate(self):
        generator = getattr(self, self.GENERATORS.get(str(self.language), self.GENERATORS["Python"]))
        result = generator()
        file_name = "{}_[{}].zip".format(self.class_name, self.language.name)
        imz = InMemoryZip()

        for res in result:
            imz.append(res["name"], res["content"])
            res["content"] = self.STYLES + highlight(
                res["content"], self.LEXERS.get(self.language, self.LEXERS["Python"]),
                self.FORMATTER)
        imz.write_to_file(file_name)
        self.code_template.created_file.delete()
        self.code_template.created_file = File(open(file_name, "rb"))
        self.code_template.save()
        os.unlink(file_name)
        return result
