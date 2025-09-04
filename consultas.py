# selecionar bebidas

consulta01 = '''
            SELECT country, total_litres_of_pure_alcohol
            FROM bebidas
            ORDER BY total_litres_of_pure_alcohol DESC
            LIMIT 10
        '''

consulta02 = '''
            SELECT AVG(beer_servings) AS cerveja, AVG (spirit_servings)
            FROM bebidas
        '''


consulta03 = '''
            SELECT beer_servings, spirit_servings, wine_servings
            FROM bebidas
         '''