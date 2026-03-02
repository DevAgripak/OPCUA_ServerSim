import asyncio
import random
import pandas as pd
import csv
from datetime import datetime
from asyncua import ua, Server

# Configurazione Server
ENDPOINT = "opc.tcp://0.0.0.0:4840/freeopcua/server/"
SERVER_NAME = "OPCUA_Sim_Agripak"
URI = "http://opcuasim.agripak.com"

# Percorsi file
TAGS_FILE = "variables/HMITags.csv"
PARQUET_FILE = "variables/CI2306-P01_2026-03-01.parquet"

class OpcuaSim:
    def __init__(self):
        self.server = Server()
        self.tags = []
        self.nodes = {}
        self.data_ranges = {}

    async def init(self):
        await self.server.init()
        self.server.set_endpoint(ENDPOINT)
        self.server.set_server_name(SERVER_NAME)
        
        # Carica struttura tag
        self.load_tags()
        # Carica range dati reali per simulazione realistica
        self.load_data_ranges()

        idx = await self.server.register_namespace(URI)
        
        # Crea la struttura DB "HMI"
        objects = self.server.nodes.objects
        hmi_db = await objects.add_object(idx, "HMI")

        # Aggiungi i nodi al server
        for tag in self.tags:
            name = tag['Name']
            dtype = tag['DataType']
            
            # Mapping tipo dato Siemens -> OPC UA
            ua_type = self.get_ua_type(dtype)
            initial_val = self.get_random_val(name, dtype)
            
            # Crea il nodo variabile
            # Per semplicità creiamo tutti i tag sotto l'oggetto HMI
            # Se ci sono sottostrutture (es. CMD_CALIBRATORE.CMD.DISCESA), 
            # potremmo creare una gerarchia di oggetti, ma per ora usiamo il nome completo
            node = await hmi_db.add_variable(idx, name, initial_val, ua_type)
            await node.set_writable()
            self.nodes[name] = (node, dtype)

    def load_tags(self):
        with open(TAGS_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                self.tags.append(row)

    def load_data_ranges(self):
        try:
            df = pd.read_parquet(PARQUET_FILE)
            for col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    self.data_ranges[col] = {
                        'min': float(df[col].min()),
                        'max': float(df[col].max())
                    }
        except Exception as e:
            print(f"Errore caricamento parquet: {e}")

    def get_ua_type(self, siemens_type):
        mapping = {
            'Bool': ua.VariantType.Boolean,
            'Real': ua.VariantType.Float,
            'LReal': ua.VariantType.Double,
            'String': ua.VariantType.String,
            'Int': ua.VariantType.Int16,
            'DInt': ua.VariantType.Int32,
            'Byte': ua.VariantType.Byte
        }
        return mapping.get(siemens_type, ua.VariantType.String)

    def get_random_val(self, name, siemens_type):
        if siemens_type == 'Bool':
            return random.choice([True, False])
        
        if siemens_type in ['Real', 'LReal']:
            if name in self.data_ranges:
                r = self.data_ranges[name]
                return random.uniform(r['min'], r['max'])
            return random.uniform(0.0, 100.0)
            
        if siemens_type == 'String':
            # Per le stringhe tipo BATCH_NomeProdotto, usiamo valori fissi o casuali
            if "Nome" in name or "Operatore" in name:
                return f"Sim_{name.split('_')[-1]}_{random.randint(1,5)}"
            return f"VAL_{random.randint(1000, 9999)}"
            
        return 0

    async def update_data(self):
        while True:
            print(f"[{datetime.now()}] Aggiornamento dati...")
            for name, (node, dtype) in self.nodes.items():
                new_val = self.get_random_val(name, dtype)
                await node.write_value(new_val)
            await asyncio.sleep(20)

    async def run(self):
        await self.init()
        async with self.server:
            print(f"Server OPC-UA avviato su {ENDPOINT}")
            await self.update_data()

if __name__ == "__main__":
    sim = OpcuaSim()
    try:
        asyncio.run(sim.run())
    except KeyboardInterrupt:
        pass
