from typing import Dict, Any, Optional, List
from pymongo.collection import Collection
from bson.objectid import ObjectId
from app.dao.interfaces import OpportunityDAO
from app.dto.models import OpportunityDTO

class MongoOpportunityDAO(OpportunityDAO):
    """
    Implementación concreta para MongoDB.
    Maneja la variabilidad de esquemas y documentos anidados.
    Fuente: Sección 4.2.3 y 6.3
    """
    def __init__(self, db):
        # Seleccionamos la colección 'opportunities'
        self.collection: Collection = db['opportunities']

    def create(self, data: Dict[str, Any]) -> str:
        # 1. Validación de Duplicados
        # Buscamos si ya existe una oferta con el mismo Título y Empresa
        # (Usamos regex para que no importe mayúsculas/minúsculas)
        existing = self.collection.find_one({
            "title": {"$regex": f"^{data.get('title')}$", "$options": "i"},
            "company_name": {"$regex": f"^{data.get('company_name')}$", "$options": "i"}
        })

        if existing:
            raise ValueError(f"Ya existe la oferta '{data.get('title')}' para la empresa '{data.get('company_name')}'.")

        # 2. Insertar si no existe
        result = self.collection.insert_one(data)
        return str(result.inserted_id)

    def get(self, id: Any) -> Optional[OpportunityDTO]:
        try:
            # IMPORTANTE: Convertir string a ObjectId para buscar en Mongo
            # Fuente: Sección 6.3 (cite 252)
            oid = ObjectId(id)
        except Exception:
            return None
    
    def get_all(self) -> List[Dict[str, Any]]:
        # Find vacío {} trae todo
        cursor = self.collection.find({})
        results = []
        for doc in cursor:
            # Transformamos el ObjectId a string para que sea serializable
            doc['id'] = str(doc.pop('_id'))
            results.append(doc)
        return results

        doc = self.collection.find_one({"_id": oid})
        if not doc:
            return None
        
        return self._map_to_dto(doc)

    def _map_to_dto(self, doc: Dict[str, Any]) -> OpportunityDTO:
        """Helper para convertir documento BSON a DTO limpio"""
        # Extraemos campos conocidos, el resto va a metadata
        return OpportunityDTO(
            id=str(doc['_id']),
            title=doc.get('title', 'Sin Título'),
            company_name=doc.get('company_name', 'Anónimo'),
            description=doc.get('description', ''),
            metadata=doc.get('requirements', {}) # Flexibilidad aquí [cite: 64]
        )

    # Implementación básica de update y delete
    def update(self, id: Any, data: Dict[str, Any]) -> bool:
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(id)}, 
                {"$set": data}
            )
            return result.modified_count > 0
        except:
            return False

    def delete(self, id: Any) -> bool:
        try:
            result = self.collection.delete_one({"_id": ObjectId(id)})
            return result.deleted_count > 0
        except:
            return False