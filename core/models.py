from django.db import models


class Language(models.Model):
    name = models.CharField(max_length=30, unique=True, verbose_name="Назва")

    def __str__(self):
        return self.name

    class Meta:
        db_table = "app_language"
        verbose_name = "Мова програмування"
        verbose_name_plural = "Мови програмування"


class Function(models.Model):
    language = models.ForeignKey(Language, null=False, related_name="functions",
                                 related_query_name="functions", verbose_name="Мова програмування")
    value = models.CharField(max_length=30, verbose_name="Значення")
    name = models.CharField(max_length=30, verbose_name="Назва")
    template = models.TextField(max_length=1500, default="", verbose_name="Код")

    def __str__(self):
        return "{} [{}]".format(self.language, self.value)

    class Meta:
        db_table = "app_function"
        verbose_name = "Функція"
        verbose_name_plural = "Функції"
        unique_together = (("language", "value"),)


class Keyword(models.Model):
    language = models.ForeignKey(Language, null=False, related_name="keywords",
                                 related_query_name="keywords", verbose_name="Мова програмування")
    value = models.CharField(max_length=30, verbose_name="Значення")
    name = models.CharField(max_length=30, verbose_name="Назва")
    template = models.TextField(max_length=1500, default="", verbose_name="Код")

    def __str__(self):
        return "{} [{}]".format(self.language, self.value)

    class Meta:
        db_table = "app_keyword"
        verbose_name = "Ключове слово"
        verbose_name_plural = "Ключові слова"
        unique_together = (("language", "value"),)


class CodeTemplate(models.Model):
    language = models.ForeignKey(Language, null=False, related_name="code_templates",
                                 related_query_name="code_templates", verbose_name="Мова програмування")
    name = models.CharField(max_length=30, verbose_name="Назва класу")
    create_dt = models.DateTimeField(auto_now_add=True, verbose_name="Дата сторення")

    class Meta:
        db_table = "app_code_template"
        verbose_name = "Шаблон коду"
        verbose_name_plural = "Шаблони коду"

    def __str__(self):
        return "{} => {} [{}]".format(self.language, self.name, self.create_dt.strftime('%Y-%m-%d %H:%M'))


class AddOnes(models.Model):
    TYPES = (
        ("int", "Integer"),
        ("float", "Real"),
        ("str", "String"),
        ("bool", "Boolean")
    )

    template = models.ForeignKey(CodeTemplate, null=False, related_name="add_ones",
                                 related_query_name="add_ones", verbose_name="Мова програмування")
    name = models.CharField(max_length=30, verbose_name="Назва")
    v_type = models.CharField(max_length=30, choices=TYPES, verbose_name="Тип")
    default = models.CharField(max_length=100, default=None, verbose_name="Значення")

    class Meta:
        db_table = "app_add_ones"
        verbose_name = "Змінна"
        verbose_name_plural = "Змінні"


class FuncAddOnes(models.Model):
    template = models.ForeignKey(CodeTemplate, null=False, related_name="add_ones_func",
                                 related_query_name="add_ones_func", verbose_name="Мова програмування")
    name = models.CharField(max_length=30, verbose_name="Назва")
    is_friend = models.BooleanField(default=False, verbose_name="Дружня")
    params = models.TextField(max_length=100, default="", verbose_name="Параметри [a,b,c=2]", blank=True)

    class Meta:
        db_table = "app_add_ones_func"
        verbose_name = "Функція"
        verbose_name_plural = "Функції"
