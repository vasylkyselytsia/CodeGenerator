from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import get_formatter_by_name
from .models import Function, Keyword


class CodeGenerator(object):

    BASIC_METHODS = ["__init__", "__ne__"]
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

    def generate_basic_functions(self):
        functions = Function.objects.filter(language=self.language, value__in=self.BASIC_METHODS)
        code = []
        for idx, f in enumerate(functions):
            func = f.template
            func = "\n".join(map(lambda x: (" " * self.INDENT) + x, func.split("\n")))
            code.append("\n" + func + "\n")

        return "\n".join(code) + "\n{another_methods}\n"

    def generate_base(self, name):
        base = Keyword.objects.filter(value='__class__', language=self.language).first()
        self.null_assertion(base)
        return str(base.template) % dict(name=name, code="{code}", variables="{variables}")

    def generate_python_code(self):
        template = self.generate_base(self.code_template.name)
        template = template.format(code=self.generate_basic_functions())
        return template

    def generate_cpp_code(self):
        template = self.generate_base(self.code_template.name)
        return template

    def generate(self):
        generator = getattr(self, self.GENERATORS.get(str(self.language), self.GENERATORS["Python"]))
        result = generator()
        result = self.STYLES + highlight(result, self.LEXERS.get(self.language, self.LEXERS["Python"]),
                                         self.FORMATTER)
        return result

