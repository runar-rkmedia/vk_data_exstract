"""Part of pdf_form_fill. Fills the database with data."""

# pylama:ignore=E402,C0413,E0611
import sys
import os
sys.path.append('../pdf_form_fill')

from helpers import commafloat
from config import configure_app
from models import (db, Manufacturor, Product,
                    ProductType)
from flask import Flask
app = Flask(__name__, instance_relative_config=True)
configure_app(app)
db.init_app(app)
print('Setup')
print(app.config['SQLALCHEMY_DATABASE_URI'])


def pop_key_from_dict_with_default(dictionary, key, default=None):
    """Pop a key from a dictionary, return it and dictionary."""
    try:
        var = dictionary.pop(key)
    except KeyError:
        var = default
    return dictionary, var


def create_products_from_list_with_product_type(products_list, product_type):
    """Create a product from list with product type."""
    for product in products_list:
        try:
            effekt = commafloat(product.pop('Effekt'))
        except KeyError as e:
            print(e)
            raise KeyError("Did not find key in {}".name)
        # Pop name of product, default to name of product_type + effekt
        product, p_name = pop_key_from_dict_with_default(
            product,
            'Betegnelse',
            default="{}-{:.0f}"
            .format(product_type.name, effekt))

        new_vk = Product(
            name=p_name,
            product_type=product_type,
            effekt=effekt)
        new_vk.add_keys_from_dict(product)


def setup_products(dictionary, ledere, manufacturor):
    """Fill the database with products, types and specs from a dictionary."""
    for name, val in dictionary.items():
        # Exstract some values from dictionary, to use for filling product_type
        val, watt_per_meter = pop_key_from_dict_with_default(
            val, 'watt_per_meter')
        val, watt_per_square_meter = pop_key_from_dict_with_default(
            val, 'watt_per_square_meter')
        val, products = pop_key_from_dict_with_default(
            val, 'products')

        # Create a ProductType
        pt = ProductType(
            name=name,
            mainSpec='TADA',
            watt_per_meter=watt_per_meter,
            watt_per_square_meter=watt_per_square_meter,
            ledere=ledere,
            manufacturor=manufacturor
        )
        # Create products with this product_type
        create_products_from_list_with_product_type(products, pt)

    db.session.commit()
    print("Database tables created")


def csv_reader(file_name, **kwargs):
    """Read a csv-file, and convert it to python-dictionary."""
    import csv
    data_list = []
    with open(file_name) as csv_file:
        has_header = csv.Sniffer().has_header(csv_file.read(1024))
        csv_file.seek(0)
        data = csv.DictReader(csv_file, **kwargs)
        if has_header and 'fieldnames' in kwargs:
            next(data)
        for csv_row in data:
            data_list.append(csv_row)
    return data_list


def csv_parse_multiple_files(path, **kwargs):
    """Parse multiple csv-files into valid data."""
    import re
    data = {}
    csv_files = []
    files = os.walk(path)
    for root, dirs, files in files: # noqa
        for file in files:
            if file.endswith(".csv"):
                csv_files.append(os.path.join(root, file))
    for file_name in csv_files:
        basename = os.path.splitext(os.path.basename(file_name))[0]
        data[basename] = {}
        data[basename]['products'] = csv_reader(file_name, **kwargs)
        wm = re.search(r"(\d+)Wm", basename)
        voltage = re.search(r"(\d+)V", basename)
        watt_per_square_meter = re.search(r"(\d+)Wkvm", basename)
        if wm:
            data[basename]['watt_per_meter'] = float(wm.groups()[0])
        if voltage:
            data[basename]['voltage'] = float(voltage.groups()[0])
        else:
            data[basename]['voltage'] = 230.0
        if watt_per_square_meter:
            data[basename]['watt_per_square_meter'] = float(
                watt_per_square_meter.groups()[0])
    return data


øglænd_kabler_headers = ['Elnr', 'Effekt', 'Lengde', 'Resistans_min',
                         'Resistans_max', 'Driftstrøm', 'Vekt']
øglænd_matter_headers = ['Elnr', 'Effekt', 'Bredde', 'Lengde', 'Areal',
                         'Resistans_min',
                         'Resistans_max', 'Driftstrøm', 'Vekt']
øglænd_kabler = csv_parse_multiple_files('data_extracts/øglænd/kabler',
                                         fieldnames=øglænd_kabler_headers)
øglænd_matter = csv_parse_multiple_files('data_extracts/øglænd/matter',
                                         fieldnames=øglænd_matter_headers)

with app.app_context():

    db.drop_all()
    db.create_all()
    Nexans = Manufacturor(name='Nexans', description="It's nexans")
    db.session.add(Nexans)
    øglænd = Manufacturor(name='Øglænd', description="It's øglænd")
    db.session.add(øglænd)

    setup_products(øglænd_kabler, 2, øglænd)
    setup_products(øglænd_matter, 2, øglænd)
