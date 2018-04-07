from django.db.models import Case, When

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import get_formatter_by_name

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
        template = self.generate_base(self.class_name)
        template = template.format(code=self.generate_basic_functions())
        return template

    def generate_cpp_code(self):

        def get_variables():
            variables = "\n"
            for v in self.code_template.add_ones.all():
                tpl = "{} {};".format(self.keywords.get(v.v_type, "int"), v.name)
                variables += ((' ' * self.INDENTS[self.language.name]) + tpl + "\n")
            return variables

        def get_includes():
            includes = ["iostream", "iomanip", "string"]
            includes = "\n".join(["#include <{}>".format(x) for x in includes])
            includes += "\n\nusing namespace std;\n\n"
            includes = "#ifndef {name}_H\n#define {name}_H\n\n".format(name=self.class_name) + includes
            return includes

        def get_basic_part():
            func_s = ["  public:\n"]
            for f in self.basic_functions:
                if f.value == "__init__":
                    func_s.append(f.template % {"class_name": self.class_name, "cppVersion": "",
                                                "body": ";", "params": ""})
                    func_s.append(f.template % {
                        "class_name": self.class_name, "cppVersion": "", "body": ";",
                        "params": "const {}& object".format(self.class_name)})
                    func_s.append(f.template % {
                        "class_name": self.class_name, "cppVersion": "", "body": ";",
                        "params": ", ".join(("{} {}".format(self.keywords.get(v.v_type, "int"), v.name)
                                             for v in self.code_template.add_ones.all()))})
                else:
                    func_s.append(f.template % {"class_name": self.class_name, "cppVersion": "", "body": ";"})
            return "\n{}".format(" " * self.INDENT).join(func_s) + "\n\n"

        def get_getter_and_setters():
            result = []
            templates = dict(Function.objects.filter(
                language=self.language, value__in=["__getattr__", "__setattr__"]).values_list("value", "template"))
            for var in self.code_template.add_ones.all():
                get_ter = templates["__getattr__"] % {
                    "variable_type": self.keywords.get(var.v_type, "int"),
                    "cppVersion": "", "body": ";",
                    "variable_cap": var.name.lower().capitalize()
                }
                set_ter = templates["__setattr__"] % {
                    "variable_type": self.keywords.get(var.v_type, "int"),
                    "cppVersion": "", "body": ";",
                    "variable_cap": var.name.lower().capitalize(),
                    "variable": var.name
                }
                result.extend([get_ter, set_ter])
            indent = " " * self.INDENT
            return "\n" + indent + "\n\n{}".format(indent).join(result)

        def add_custom_functions():
            result = []
            for func in self.code_template.add_ones_func.all():
                result.append(self.keywords["__function__"] % {
                    "f_type": func.f_type, "name": func.name,
                    "cppVersion": "", "body": ";"
                })
            indent = " " * self.INDENT
            return "\n" + indent + "\n\n{}".format(indent).join(result)

        template = get_includes() + self.generate_base(self.class_name)
        template = template.replace("{variables}", "%(variables)s")
        template = template.replace("{code}", "%(code)s")
        basic_func = self.generate_basic_functions()
        basic_func %= {"class_name": self.class_name, "body": ";", "cppVersion": ""}
        basic_func = get_basic_part() + basic_func.format(another_methods=get_getter_and_setters())
        basic_func += add_custom_functions()

        template %= {"code": basic_func, "variables": get_variables()}
        return template + "\n\n#endif // {}_H".format(self.class_name)

    def generate(self):
        generator = getattr(self, self.GENERATORS.get(str(self.language), self.GENERATORS["Python"]))
        result = generator()
        result = self.STYLES + highlight(result, self.LEXERS.get(self.language, self.LEXERS["Python"]),
                                         self.FORMATTER)
        return result

