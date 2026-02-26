from django.shortcuts import render

def paie_client_dashboard(request):
    return render(request, "paie/client/dashboard.html")
