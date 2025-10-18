from django.shortcuts import render
from django.views import View

class SystemView(View):
    template_name = "system.html"

    def get(self, request):
        return render(request, self.template_name)
