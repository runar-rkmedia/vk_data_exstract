

from pprint import pprint
import sys
import os

sys.path.append('../pdf_form_fill')
os.chdir('../pdf_form_fill/')



def setup_products():
    """Fill the database with products, types and specs from csv."""
    print(os.getcwd())
    from config import configure_app
    from models import (db, Manufacturor, Product,
                        ProductSpec, ProductType, lookup_vk)
    from flask import Flask
    app = Flask(__name__, instance_relative_config=True)
    configure_app(app)
    db.init_app(app)
    print('Setup')
    print(app.config['SQLALCHEMY_DATABASE_URI'])
    with app.app_context():
        db.drop_all()
        db.create_all()
        Nexans = Manufacturor(name='Nexans', description="It's nexans")
        db.session.add(Nexans)
        øglænd = Manufacturor(name='Øglænd', description="It's øglænd")
        db.session.add(øglænd)
        txlp17 = ProductType(name='TXLP/2R/17',
                             mainSpec='TXLP',
                             watt_per_meter=17,
                             ledere=2,
                             manufacturor=Nexans)
        db.session.add(txlp17)
        txlp10 = ProductType(name='TXLP/2R/10',
                                  mainSpec='TXLP',
                                  watt_per_meter=10,
                                  ledere=2,
                                  manufacturor=Nexans)
        db.session.add(txlp10)
        import Nexans_TXLP
        for vk in Nexans_TXLP.vks:
            name = vk.pop('Betegnelse')
            effekt = vk.pop('Effekt ved 230V')
            if name[-2:] == '17':
                product_type = txlp17
            else:
                product_type = txlp10
            if name:
                new_vk = Product(
                    name=name, product_type=product_type, effekt=effekt)
                new_vk.add_keys_from_dict(vk)
                db.session.add(new_vk)
        db.session.commit()
        print("Database tables created")

setup_products()


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
    import os
    import re
    data = {}
    csv_files = []
    files = os.walk(path)
    for root, dirs, files in files:
        for file in files:
            if file.endswith(".csv"):
                csv_files.append(os.path.join(root, file))
    for file_name in csv_files:
        basename = os.path.splitext(os.path.basename(file_name))[0]
        data[basename] = {}
        data[basename]['products'] = csv_reader(file_name, **kwargs)
        keys = {}
        wm = re.search("(\d+)Wm", basename)
        voltage = re.search("(\d+)V", basename)
        watt_per_square_meter = re.search("(\d+)Wkvm", basename)
        if wm:
            data[basename]['watt_per_meter'] = float(wm.groups()[0])
        else:
            data[basename]['voltage'] = 230.0
        if watt_per_square_meter:
            data[basename]\
                ['watt_per_square_meter'] = float(watt_per_square_meter.groups()[0])
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


# print(len(øglænd_kabler))
# for table in øglænd_kabler:

# pprint(øglænd_matter)


# print(files)


for key, val in øglænd_kabler.items():
    name = key
    try:
        watt_per_meter = val.pop('watt_per_meter')
    except KeyError:
        watt_per_meter = None
    try:
        voltage = val.pop('voltage', 230)
    except KeyError:
        voltage = 230
    try:
        watt_per_square_meter = val.pop('watt_per_square_meter')
    except KeyError:
        watt_per_square_meter = None
    try:
        products = val.pop('products')
    except KeyError:
        products = None

    print(name, watt_per_meter, voltage, watt_per_square_meter)
    # pt = ProductType(name='key',
    #                      mainSpec='TXLP',
    #                      watt_per_meter=17,
    #                      ledere=2,
    #                      manufacturor=Nexans)
    # pprint(key)
