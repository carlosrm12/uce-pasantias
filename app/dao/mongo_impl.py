from typing import Dict, Any, Optional, List
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError
from bson.objectid import ObjectId
from app.dao.interfaces import OpportunityDAO
from app.dto.models import OpportunityDTO
import pybreaker
import logging

# --- CONFIGURACIÓN DEL CIRCUIT BREAKER ---
db_breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=10)

class MongoOpportunityDAO(OpportunityDAO):
    def __init__(self, connection_uri: str):
        # Fail Fast: 2 segundos máximo
        self.client = MongoClient(
            connection_uri, 
            serverSelectionTimeoutMS=2000,
            connectTimeoutMS=2000,
            socketTimeoutMS=2000
        )
        self.db = self.client['ucedb']
        self.collection: Collection = self.db['opportunities']

    # ---------------------------------------------------------
    # CREATE
    # ---------------------------------------------------------
    def create(self, data: Dict[str, Any]) -> str:
        return self._protected_create(data)

    @db_breaker
    def _protected_create(self, data: Dict[str, Any]) -> str:
        # VALIDACIÓN DE DUPLICADOS
        existing = self.collection.find_one({
            "title": {"$regex": f"^{data.get('title')}$", "$options": "i"},
            "company_name": {"$regex": f"^{data.get('company_name')}$", "$options": "i"}
        })
        if existing:
            raise ValueError(f"Ya existe la oferta '{data.get('title')}' para '{data.get('company_name')}'.")

        result = self.collection.insert_one(data)
        return str(result.inserted_id)

    # ---------------------------------------------------------
    # GET ALL (Lista de Ofertas)
    # ---------------------------------------------------------
    def get_all(self) -> List[Dict[str, Any]]:
        try:
            return self._protected_get_all()
        
        except pybreaker.CircuitBreakerError:
            logging.warning("⚠️ Circuit Breaker ABIERTO.")
            return self._get_maintenance_card()
            
        except Exception as e:
            # Capturamos el Timeout de 2s aquí
            logging.error(f"Error Mongo get_all: {e}")
            return self._get_maintenance_card() 

    @db_breaker
    def _protected_get_all(self) -> List[Dict[str, Any]]:
        # ¡SIN TRY/EXCEPT! Si falla, explota para activar el Breaker
        cursor = self.collection.find({})
        results = []
        for doc in cursor:
            doc['id'] = str(doc.pop('_id'))
            results.append(doc)
        return results

    # ---------------------------------------------------------
    # GET (Una Oferta)
    # ---------------------------------------------------------
    def get(self, id: Any) -> Optional[OpportunityDTO]:
        try:
            return self._protected_get(id)
            
        except pybreaker.CircuitBreakerError:
            return self._get_maintenance_dto(id)
            
        except Exception as e:
            logging.error(f"Error Mongo get individual: {e}")
            return self._get_maintenance_dto(id)

    @db_breaker
    def _protected_get(self, id: Any) -> Optional[OpportunityDTO]:
        try:
            oid = ObjectId(id)
        except:
            return None # ID inválido

        doc = self.collection.find_one({"_id": oid})
        
        if not doc:
            return None
        return self._map_to_dto(doc)

    # ---------------------------------------------------------
    # UPDATE (IMPLEMENTADO ✅)
    # ---------------------------------------------------------
    def update(self, id: Any, data: Dict[str, Any]) -> bool:
        """
        Actualiza una oferta existente.
        No usamos decorador aquí para manejar el error manualmente en la API.
        """
        try:
            oid = ObjectId(id)
            # $set asegura que solo se actualicen los campos enviados
            result = self.collection.update_one({"_id": oid}, {"$set": data})
            # matched_count > 0 significa que encontró el ID, aunque no haya cambios
            return result.matched_count > 0
        except Exception as e:
            logging.error(f"Error update Mongo: {e}")
            return False

    # ---------------------------------------------------------
    # DELETE (IMPLEMENTADO ✅)
    # ---------------------------------------------------------
    def delete(self, id: Any) -> bool:
        """
        Elimina una oferta por ID.
        """
        try:
            oid = ObjectId(id)
            result = self.collection.delete_one({"_id": oid})
            return result.deleted_count > 0
        except Exception as e:
            logging.error(f"Error delete Mongo: {e}")
            return False

    # ---------------------------------------------------------
    # HELPERS
    # ---------------------------------------------------------
    def _map_to_dto(self, doc: Dict[str, Any]) -> OpportunityDTO:
        return OpportunityDTO(
            id=str(doc['_id']),
            title=doc.get('title', 'Sin Título'),
            company_name=doc.get('company_name', 'Anónimo'),
            description=doc.get('description', ''),
            metadata=doc.get('requirements', {})
        )

    def _get_maintenance_card(self):
        return [{
            "id": "maintenance",
            "title": "🔴 Sistema en Mantenimiento",
            "company_name": "Intente más tarde",
            "description": "Base de datos temporalmente no disponible.",
            "requirements": {}
        }]

    def _get_maintenance_dto(self, id):
        return OpportunityDTO(
            id=str(id),
            title="Oferta no disponible",
            company_name="Sistema Offline",
            description="Mantenimiento",
            metadata={}
        )