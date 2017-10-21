"""Part of pdf_form_fill. Fills the database with data."""
# !venv/bin/python
# pylama:ignore=E402,C0413,E0611
import sys
import os
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

from pdf_filler.helpers import commafloat
from config import configure_app
from models import db
from models_product import (
    Manufacturor,
    Product,
    ProductType,
)
from models_credentials import (
    Company,
    User,
    Address,
    ContactType,
    Invite,
    RoomTypeInfo
)
from flask import Flask
from rooms import rooom_info_list


def dictionary_subset(dictionary, list_of_keys):
    """Only return the data we want from a dictionary."""
    d = {}
    for key, value in dictionary.items():
        if key not in list_of_keys:
            continue
        if value is not "":
            try:
                if value is not float:
                    value = commafloat(value)
            except (AttributeError, ValueError) as e:
                pass
            d.update({key: value})
    return d


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
            restrictions['R_min'] = commafloat(
                product.pop('R_min'))
        if product.get('R_max'):
            restrictions['R_max'] = commafloat(product.pop('R_max'))
        if product.get('R_nom'):
            restrictions['R_nom'] = commafloat(product.pop('R_nom'))
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
        try:
            val['inside']
        except KeyError:
            print('MISSING', val, val.get('Type'))
        pt = ProductType(
            name=val.get('Type'),
            description=val.get('Description'),
            mainSpec=val.get('MainSpec'),
            secondarySpec=val['Voltage'],
            isMat=val['isMat'],
            self_limiting=val.get('self_limiting', False),
            per_meter=val.get('per_meter', False),
            outside=val['outside'],
            inside=val['inside'],
            manufacturor=manufacturor
        )
        # Create products with this product_type
        create_products_from_list_with_product_type(val['products'], pt)

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
    data = {}
    csv_files = []
    files = os.walk(path)
    for root, dirs, files in files:  # noqa
        for file in files:
            if file.endswith(".csv"):
                csv_files.append(os.path.join(root, file))
    print(csv_files)
    for file_name in csv_files:
        csv_dictionary = csv_reader(file_name, **kwargs)
        print('reading ', file_name)
        for row in csv_dictionary:

            this_name = "{}{}{}".format(
                row.get('Type'),
                row.get('MainSpec'),
                row.get('Voltage')
            )
            if not data.get(this_name):
                data[this_name] = dictionary_subset(
                    row,
                    {
                        'Voltage',
                        'Type',
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
            data[this_name]['outside'] = row['outside']
            data[this_name]['inside'] = row['inside']
            data[this_name]['self_limiting'] = row['self_limiting']
            data[this_name]['per_meter'] = row['per_meter']
            data[this_name]['isMat'] = row['isMat']
    return data


app = Flask(__name__, instance_relative_config=True)
configure_app(app)
db.init_app(app)
print('Setup')
print(app.config['SQLALCHEMY_DATABASE_URI'])
print(app.config['SQLALCHEMY_BINDS'])


def populate_db():
    """Description."""
    with app.app_context():
        if 'empty' in sys.argv:
            Product.query.delete()
            ProductType.query.delete()
            Manufacturor.query.delete()
            db.session.commit()
            print('Emptied table Product')
            print('Emptied table ProductType')
            print('Emptied table Manufacturor')
        count = Product.query.count()
        count += ProductType.query.count()
        count += Manufacturor.query.count()
        if count > 0:
            print('Table is not empty., quitting. Append "empty" to empty it.')
            return
        teste_firma = Company.query.filter_by(name='Testing company').first()
        if not teste_firma:
            test_adresse = Address(
                address1='Testeveien',
                post_code=0000,
                post_area='Testestedet'
            )
            db.session.add(test_adresse)
            teste_firma = Company(
                name='Testing company',
                description='testefirma',
                orgnumber=980980980,
                address=test_adresse,
                contact_name="John Doe",
                contact_email="john@doe.com",
                contact_phone=12312312
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


def create_rooms():
    """Create info for rooms."""
    with app.app_context():
        if 'empty' in sys.argv:
            RoomTypeInfo.query.delete()
            print('Emptied table RoomTypeInfo')
        count = RoomTypeInfo.query.count()
        if count > 0:
            print('Table is not empty., quitting. Append "empty" to empty it.')
            return
        for room in rooom_info_list:
            db.session.add(RoomTypeInfo(
                names=room['names'],
                maxEffect=room['maxEffect'],
                normalEffect=room['normalEffect'],
                outside=room.get('outside', False)
            ))

        db.session.commit()
        print('Added all rooms')


# hook up extensions to app
if __name__ == "__main__":
    if 'create' in sys.argv:
        with app.app_context():
            db.create_all()
    if 'products' in sys.argv:
        populate_db()
    if 'rooms' in sys.argv:
        create_rooms()
