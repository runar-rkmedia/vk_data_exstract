Dette er en del av varmekabel-prosjektet. Denne delen fyller databasen med data fra produsenter.


#### mangler-øglænd:

Lime,,Plug and play, K3, Betonghering, Frostsikring, Marine


## For å hente ut data:

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
pg_dump vk_products > vk_products.sql
pg_dump varmekabler > varkekabler.sql
cat vk_products.sql | heroku pg:psql varmekabler-products
cat varkekabler.sql | heroku pg:psql varmekabler-main-db
```
