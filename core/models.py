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

    def __str__(self):
        return "{} [{}]".format(self.language, self.value)

    class Meta:
        db_table = "app_keyword"
        verbose_name = "Ключове слово"
        verbose_name_plural = "Ключові слова"
        unique_together = (("language", "value"),)
