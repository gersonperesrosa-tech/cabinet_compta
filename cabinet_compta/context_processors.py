def user_role(request):
    if not request.user.is_authenticated:
        return {"base_template": "base.html"}

    groups = request.user.groups.values_list("name", flat=True)

    if "Client" in groups:
        return {"base_template": "base_paie_client.html"}

    if "Partenaire" in groups:
        return {"base_template": "base_partenaire.html"}

    return {"base_template": "base.html"}
