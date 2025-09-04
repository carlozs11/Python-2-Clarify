class Carro:
    def __init__(self, modelo, cor):
        self.modelo = modelo
        self.cor = cor
        self.velocidade = 0 # o carro começa parado

    def acelerar(self, incremento):
            self.velocidade += incremento
            print(f'A montana {self.modelo} acelerou para {self.velocidade} Km/h.')

    def desacelerar(self, decremento):
         self.velocidade -= decremento
         print(f'A {self.modelo} desacelerou para {self.velocidade} Km/h.')

meu_carro = Carro('Montana', 'Prata', )
outro_carro = Carro('Golf', 'Vermelho')

# usando os metódos
meu_carro.acelerar(20)
meu_carro.acelerar(20)
meu_carro.acelerar(20)
meu_carro.desacelerar(10)
