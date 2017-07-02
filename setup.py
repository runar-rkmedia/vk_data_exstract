"""Part of pdf_form_fill. Fills the database with data."""
#!venv/bin/python
# pylama:ignore=E402,C0413,E0611
import sys
import os
from pprint import pprint  # noqa
sys.path.append('../pdf_form_fill')

from field_dicts.helpers import commafloat
from config import configure_app
from models import (db, Manufacturor, Product,
                    ProductType, Company, User, Address, ContactType,
                    Invite, ProductCatagory)
from flask import Flask


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

        product, effect = pop_key_from_dict_with_default(product, 'Effect')
        # Pop name of product, default to name of product_type + effect
        restrictions = {}
        if product.get('R_min'):
            restrictions['R_min'] = product.pop('R_min')
        if product.get('R_max'):
            restrictions['R_max'] = product.pop('R_max')
        if product.get('R_nom'):
            restrictions['R_nom'] = product.pop('R_nom')
        new_vk = Product(
            id=product.pop('El-number'),
            name=product.pop('Name'),
            product_type=product_type,
            effect=effect,
            restrictions=restrictions,
            specs=product,
            )
        db.session.add(new_vk)


def setup_products(dictionary, ledere, manufacturor):
    """Fill the database with products, types and specs from a dictionary."""
    for name, val in dictionary.items():
        # Create a ProductType
        pt = ProductType(
            name=name,
            description=val.get('Description'),
            mainSpec=val['MainSpec'],
            secondarySpec=val['Voltage'],
            catagory=val['catagory'],
            manufacturor=manufacturor
        )
        # Create products with this product_type
        create_products_from_list_with_product_type(val['products'], pt)

    db.session.commit()
    print("Database tables created")


def dictionary_subset(dictionary, list_of_keys):
    """Only return the data we want from a dictionary."""
    return {k: dictionary[k] for k in dictionary.keys() & list_of_keys if dictionary[k] is not ""}


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


def get_product_catagory(outside, mat):
    """Return the correct product_type."""
    if mat and outside:
        return ProductCatagory.mat_outside
    if not mat and outside:
        return ProductCatagory.cable_outside
    if mat and not outside:
        return ProductCatagory.mat_inside
    if not mat and not outside:
        return ProductCatagory.cable_inside


def csv_parse_multiple_files(path, **kwargs):
    """Parse multiple csv-files into valid data."""
    import re
    data = {}
    csv_files = []
    files = os.walk(path)
    for root, dirs, files in files:  # noqa
        for file in files:
            if file.endswith(".csv"):
                csv_files.append(os.path.join(root, file))
    for file_name in csv_files:
        csv_dictionary = csv_reader(file_name, **kwargs)
        for row in csv_dictionary:
            this_name = row['Type']
            if not data.get(this_name):
                data[this_name] = dictionary_subset(
                    row,
                    {
                        'Voltage',
                        'MainSpec',
                        'isMat',
                        'outside',
                        'Description'
                    })
            if not data[this_name].get('products'):
                data[this_name]['products'] = []
            data[this_name]['products'].append(dictionary_subset(
                row,
                {
                    'El-number',
                    'Effect',
                    'Name',
                    'ArtNr',
                    'R_nom',
                    'R_min',
                    'R_max',
                    'ArtNr',
                    'Area',
                    'Width',
                    'Length',
                }))
            data[this_name]['catagory'] = get_product_catagory(
                row['outside'] == 'FALSE',
                row['isMat'] == 'TRUE'
            )
    return data


def populate_db():
    """Description."""
    app = Flask(__name__, instance_relative_config=True)
    configure_app(app)
    db.init_app(app)
    print('Setup')
    print(app.config['SQLALCHEMY_DATABASE_URI'])
    print(app.config['SQLALCHEMY_BINDS'])
    with app.app_context():

        # db.drop_all()
        # db.create_all()
        db.drop_all(bind=['products'])
        db.create_all(bind=['products'])
        test_adresse = Address(
            line1='Testeveien',
            postnumber=0000,
            postal='Testestedet'
        )
        db.session.add(test_adresse)
        teste_firma = Company(
            name='Testing company',
            description='testefirma',
            orgnumber=980980980,
            address=test_adresse
        )
        db.session.add(teste_firma)
        testUser = User(
            given_name='Test',
            role='companyAdmin',
            family_name='Testson',
            email='TestyTestson@test.com',
            title='King',
            company=teste_firma
        )
        db.session.add(testUser)
        testUser.add_contact(
            type=ContactType.phone,
            value='980489590',
            description='test'
        )
        inviteCompany = Invite(
            id=Invite.get_random_unique_invite_id(),
            company=teste_firma,
            type='company',
            inviter=testUser)
        inviteCreate = Invite(
            id=Invite.get_random_unique_invite_id(),
            type='create_company',
            inviter=testUser)
        print('inviteCompany:', inviteCompany.id)
        print('inviteCreate:', inviteCreate.id)
        db.session.add(inviteCompany)
        db.session.add(inviteCreate)
        Nexans = Manufacturor(name='Nexans', description="Inn i varmen")
        db.session.add(Nexans)
        Thermofloor = Manufacturor(name='Thermofloor', description="")
        db.session.add(Thermofloor)
        øglænd = Manufacturor(name='Øglænd', description="")
        db.session.add(øglænd)

        setup_products(øglænd_kabler, 2, øglænd)
        setup_products(nexans_kabler, 2, Nexans)
        setup_products(thermofloor_kabler, 2, Thermofloor)


øglænd_kabler_headers = ['Elnr', 'Effekt', 'Lengde', 'Resistans_min',
                         'Resistans_max', 'Driftstrøm', 'Vekt']
øglænd_matter_headers = ['Elnr', 'Effekt', 'Bredde', 'Lengde', 'Areal',
                         'Resistans_min',
                         'Resistans_max', 'Driftstrøm', 'Vekt']
nexnans_kabler_headers = ['Betegnelse',
                          'Effekt', 'Lengde', 'Nominell elementmotstand',
                          'Ytre dimensjoner', 'Vekt', 'Elnr',
                          'Nexans art. nr.', 'GTIN']
øglænd_kabler = csv_parse_multiple_files('data_extracts/oegleand/')
nexans_kabler = csv_parse_multiple_files('data_extracts/nexans/')
thermofloor_kabler = csv_parse_multiple_files('data_extracts/thermofloor/')


populate_db()
