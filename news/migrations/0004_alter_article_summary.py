# Generated by Django 5.2.4 on 2025-07-23 17:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0003_article_link_article_source'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='summary',
            field=models.TextField(blank=True, null=True),
        ),
    ]
