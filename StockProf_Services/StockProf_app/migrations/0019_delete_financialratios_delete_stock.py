# Generated by Django 4.0.5 on 2023-03-30 10:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('StockProf_app', '0018_my_stockprice'),
    ]

    operations = [
        migrations.DeleteModel(
            name='financialRatios',
        ),
        migrations.DeleteModel(
            name='Stock',
        ),
    ]
