from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import View

from core.generator import CodeGenerator


class BaseView(View):

    template_name = "base.html"

    def get(self, request):
        cg = CodeGenerator("Python")
        print(cg.base_template)
        return render(request, self.template_name, {})
