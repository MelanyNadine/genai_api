# Generated by Django 5.1 on 2024-08-14 19:06

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_rename_name_files_filename_remove_files_encodedfile_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="files",
            name="filedata",
            field=models.FileField(upload_to=""),
        ),
    ]
