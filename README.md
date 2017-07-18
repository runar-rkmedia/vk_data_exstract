Dette er en del av varmekabel-prosjektet. Denne delen fyller databasen med data fra produsenter.


#### mangler-øglænd:

Lime,,Plug and play, K3, Betonghering, Frostsikring, Marine


## For å hente ut data:

Google Spreadsheet har regex-funksjon, noe som gjør det enklere å hente ut data fra ugunstige kilder. Det er laget et regneark på adressen nedenfor:

[Googe Spreadsheet document](https://docs.google.com/spreadsheets/d/1j4J6n0836Zhil9D4LMsfyUJ5iwtncNsf4T8eDcrwc0A/edit#gid=0)

Bruk tabular, velg enkelt-tabeller, bruk metoden Lettuce, og eksporter. Navnet på csv-filen skal være typen varmekabler, i følgende format:
 ```
 ØS-Snøkabel-Lett-30-30Wm-400V.csv # 30watt per meter, 400 volt
 ØS-Snømatte-300Wkm # 300watt per kvadratmeter

 ```


 utelatte data blir ikke tatt med i parseren.

## Dumping local database to heroku

Reset the database (not destroy) on heroku.com

run locally:
```
pg_dump --data-only vk_products > vk_products.sql
pg_dump --data-only varmekabler > varkekabler.sql
cat vk_products.sql | heroku pg:psql varmekabler-products
cat varkekabler.sql | heroku pg:psql varmekabler-main-db
```
