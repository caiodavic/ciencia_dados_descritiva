import scrapy
import os
GASTOS = ['TOTAL','JAN','FEV','MAR','ABR','MAI','JUN','JUL','AGO','SET','OUT','NOV','DEZ']

class DeputadosSpider(scrapy.Spider):
    name = 'deputados'
    allowed_domains = ['www.camara.leg.br']
    start_urls = ['https://www.camara.leg.br/deputados/']

    def parse(self, response):
        deputado = {}
        infos = self.get_infos(response)
        presencas = self.get_presencas(response)
        gastos_parlamentar, gastos_gabinete = self.get_gastos(response)
        salario = self.get_salario(response)
        viagem = self.get_viagem(response)
        
        deputado['nome'] = infos['nome_civil']
        deputado['genero'] = infos['genero']
        deputado['data_nascimento'] = infos['data_de_nascimento']
        deputado['presença_plenario'] = presencas[0]        
        deputado['ausencia_justificada_plenario'] = presencas[1]
        deputado['ausencia_plenario'] = presencas[2]
        deputado['presença_comissao'] = presencas[3]        
        deputado['ausencia_justificada_comissao'] = presencas[4]
        deputado['ausencia_comissao'] = presencas[5]
        deputado = self._put_gastos(gastos_gabinete,gastos_parlamentar,deputado)
        deputado['salario'] = salario
        deputado['viagem'] = viagem
        
        yield deputado

    def _put_gastos(self,gab,par,dep):
        for i in GASTOS:
            mes = i.lower()
            dep[f'gasto_{mes}_par,'] = par[i]
        for i in GASTOS:
            mes = i.lower()
            dep[f'gasto_{mes}_gab,'] = gab[i]
        return dep

    def start_requests(self):       
        urls = self.get_urls("../data/")        
        for i in urls:               
            yield scrapy.Request(i[0], callback = self.parse, meta={'gender':i[1]})
        print('Finalizado')

    def get_urls(self,path):
        urls = []
        
        for file_path in os.listdir(path):
            if(file_path.split('_')[1].endswith('as')):
                gender = 'female'
            else:
                gender = 'male'
            with open(f'{path}{file_path}',"r") as file:
                files = file.readlines()
                for url in files:
                    url = url.replace('"','')
                    url = url.strip()
                    url = url.replace(',','')
                    urls.append((url,gender))        
        
        return urls
    

    def get_viagem(self,response):
        viagem = int(response.css("ul.recursos-beneficios-deputado-container li div.beneficio .beneficio__info::text").getall()[-2])
        return viagem
        

    def get_salario(self,response):
        beneficio = response.css("div.beneficio a::text").getall()
        salario = self.convert_number(beneficio[3].split()[1])        
        return salario

    def get_gastos(self,response):        
        gastos_par, gastos_gab = self._init_gastos()

        for idx,i in enumerate((response.css("li.gasto"))):      
            flag_par = False
            if idx == 0:
                flag_par = True
            for j in (i.css("tr")):
                gasto = (j.css("td::text").getall())
                if gasto == []:
                    continue
                if flag_par:
                    gastos_par = self._aux_gastos(gastos_par,gasto)
                else:
                    gastos_gab = self._aux_gastos(gastos_gab,gasto)
        return gastos_par, gastos_gab            
    
    def _aux_gastos(self,dict_gastos,vetor_gastos):
        valor = self.convert_number(vetor_gastos[1])
        if vetor_gastos[0] == 'Total Gasto':
            dict_gastos['TOTAL'] = valor
        else:
            dict_gastos[vetor_gastos[0]] = valor
        return dict_gastos
    
    def _init_gastos(self):
        dict_par = {}
        dict_gab = {}
        for i in GASTOS:
            dict_par[i] = 0
            dict_gab[i] = 0

        return dict_par,dict_gab

    def get_presencas(self,response):
        presencas = []
        for i in (response.css("dd.list-table__definition-description::text").getall()):            
            presencas.append(int(i.strip().split()[0]))

        return presencas
        
    def get_infos(self,response):
        infos = {}
        for i in (response.css("ul.informacoes-deputado li")):            
            key = i.css('span::text').getall()[0].lower().strip().replace(" ", "_")[:-1]            
            infos[key] = i.css('li::text').getall()[0].strip() 
        infos['genero'] = response.meta.get('gender')    
        return infos    

    def convert_number(self,number):
        number = number.replace(',','')
        number = number.replace('.','')
        number = float(number)/100
        return number

    

        