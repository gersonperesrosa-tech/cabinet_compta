from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("dossiers", "0025_urssafmensuelle_urssaftrimestrielle")]
    operations = [migrations.AddField(model_name="tvadeclaration", name="responsable_declaration", field=models.CharField(max_length=3, blank=True, default=""))]
