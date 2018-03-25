from django.db.models import Q
from .models import Language, Function, Keyword


class CodeGenerator(object):

    BASIC_METHODS = ["__init__", "__ne__"]
    INDENT = 4

    @staticmethod
    def assert_language(obj):
        assert obj is not None, "Invalid Language Given"

    def __init__(self, language, **options):
        filters = {"id": language} if isinstance(language, int) else {"name": language}
        self.language = Language.objects.filter(**filters).first()
        self.assert_language(self.language)
        self.base_template = self.generate_base(options.get("class_name", "Main"))
        self.base_template = self.base_template.format(code=self.generate_basic_functions())
        # with open("test.txt", "w") as f:
        #     f.write(self.base_template.replace('\n\n', '\n'))

    def generate_basic_functions(self):
        functions = Function.objects.filter(language=self.language, value__in=self.BASIC_METHODS)
        code = []
        for idx, f in enumerate(functions):
            func = f.template
            func = "\n".join(map(lambda x: (" " * self.INDENT) + x, func.split("\n")))
            code.append("\n" + func + "\n")

        return "\n".join(code) + "\n{another_methods}\n"

    def generate_base(self, name):
        base = Keyword.objects.filter(value='__class__').first()
        self.assert_language(base)
        print(base.template)
        return str(base.template) % dict(name=name, code="{code}")


# cg = CodeGenerator("Python")
# print(cg.base_template.format(code="\t{}".format(Function.objects.get(language=1, value="__init__").template)))
