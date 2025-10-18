from django.views import View
from django.shortcuts import render

class FrontendAppView(View):
    def get(self, request):
        # Render index.html template
        return render(request, "index.html")
