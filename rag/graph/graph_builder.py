import json
import networkx as nx
from pathlib import Path
from typing import List, Optional
from .schema import Node, Relation, NodeType, RelationType


class KnowledgeGraphBuilder:
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.nodes: dict[str, Node] = {}
        self.relations: List[Relation] = []
    
    def add_node(self, node: Node) -> None:
        self.nodes[node.id] = node
        self.graph.add_node(
            node.id,
            type=node.type.value,
            label=node.label,
            description=node.description,
            source=node.source
        )
    
    def add_relation(self, relation: Relation) -> None:
        if relation.source_id not in self.nodes:
            raise ValueError(f"Nodo origen '{relation.source_id}' no existe")
        if relation.target_id not in self.nodes:
            raise ValueError(f"Nodo destino '{relation.target_id}' no existe")
        
        self.relations.append(relation)
        self.graph.add_edge(
            relation.source_id,
            relation.target_id,
            type=relation.type.value,
            weight=relation.weight,
            condition=relation.condition,
            source=relation.source
        )
    
    def save(self, filepath: str | Path) -> None:
        data = {
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "relations": [r.to_dict() for r in self.relations]
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load(self, filepath: str | Path) -> None:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        self.graph.clear()
        self.nodes.clear()
        self.relations.clear()
        
        for node_data in data["nodes"]:
            self.add_node(Node.from_dict(node_data))
        
        for rel_data in data["relations"]:
            self.add_relation(Relation.from_dict(rel_data))


def build_viticulture_graph() -> KnowledgeGraphBuilder:
    
    builder = KnowledgeGraphBuilder()
    
    variables_climaticas = [
        Node(
            id="temperatura_baja",
            type=NodeType.VARIABLE_CLIMATICA,
            label="Temperatura baja",
            description="Temperatura mínima inferior al umbral óptimo del cultivo",
            source="Hidalgo, L. (2002). Tratado de Viticultura General"
        ),
        Node(
            id="temperatura_alta",
            type=NodeType.VARIABLE_CLIMATICA,
            label="Temperatura alta",
            description="Temperatura máxima superior al umbral de estrés térmico",
            source="Hidalgo, L. (2002). Tratado de Viticultura General"
        ),
        Node(
            id="humedad_alta",
            type=NodeType.VARIABLE_CLIMATICA,
            label="Humedad relativa alta",
            description="Humedad relativa superior al 80%",
            source="Reynier, A. (2012). Manual de Viticultura"
        ),
        Node(
            id="precipitacion_escasa",
            type=NodeType.VARIABLE_CLIMATICA,
            label="Precipitación escasa",
            description="Precipitación acumulada inferior a las necesidades hídricas",
            source="FAO. (2006). Evapotranspiración del cultivo"
        ),
        Node(
            id="viento_fuerte",
            type=NodeType.VARIABLE_CLIMATICA,
            label="Viento fuerte",
            description="Velocidad del viento superior a 50 km/h",
            source="MAPA. Guía de gestión integrada de plagas"
        ),
        Node(
            id="temperatura_bajo_cero",
            type=NodeType.VARIABLE_CLIMATICA,
            label="Temperatura bajo cero",
            description="Temperatura mínima inferior a 0°C",
            source="Hidalgo, L. (2002). Tratado de Viticultura General"
        ),
    ]
    
    for node in variables_climaticas:
        builder.add_node(node)

    riesgos = [
        Node(
            id="helada",
            type=NodeType.RIESGO,
            label="Riesgo de helada",
            description="Daño por congelación del agua en tejidos vegetales",
            source="Hidalgo, L. (2002). Tratado de Viticultura General"
        ),
        Node(
            id="estres_termico",
            type=NodeType.RIESGO,
            label="Estrés térmico",
            description="Daño fisiológico por temperaturas extremas superiores a 35°C",
            source="Keller, M. (2015). The Science of Grapevines"
        ),
        Node(
            id="estres_hidrico",
            type=NodeType.RIESGO,
            label="Estrés hídrico",
            description="Déficit de agua que afecta funciones fisiológicas",
            source="FAO. (2006). Evapotranspiración del cultivo"
        ),
    ]
    
    for node in riesgos:
        builder.add_node(node)
    
    enfermedades = [
        Node(
            id="mildiu",
            type=NodeType.ENFERMEDAD,
            label="Mildiu",
            description="Enfermedad causada por Plasmopara viticola. Requiere humedad >80% y temperatura 10-25°C",
            source="MAPA. Guía de gestión integrada de plagas de la vid"
        ),
        Node(
            id="oidio",
            type=NodeType.ENFERMEDAD,
            label="Oídio",
            description="Enfermedad causada por Erysiphe necator. Favorecida por temperaturas 20-27°C",
            source="MAPA. Guía de gestión integrada de plagas de la vid"
        ),
        Node(
            id="botrytis",
            type=NodeType.ENFERMEDAD,
            label="Botrytis",
            description="Podredumbre gris causada por Botrytis cinerea",
            source="Reynier, A. (2012). Manual de Viticultura"
        ),
    ]
    
    for node in enfermedades:
        builder.add_node(node)
    
    componentes = [
        Node(
            id="brotes",
            type=NodeType.COMPONENTE_VID,
            label="Brotes",
            description="Tejido joven muy sensible a heladas y estrés",
            source="Reynier, A. (2012). Manual de Viticultura"
        ),
        Node(
            id="hojas",
            type=NodeType.COMPONENTE_VID,
            label="Hojas",
            description="Órganos fotosintéticos, afectados por enfermedades fúngicas",
            source="Hidalgo, L. (2002). Tratado de Viticultura General"
        ),
        Node(
            id="racimos",
            type=NodeType.COMPONENTE_VID,
            label="Racimos",
            description="Órganos reproductivos, sensibles a podredumbres",
            source="Reynier, A. (2012). Manual de Viticultura"
        ),
        Node(
            id="vigor",
            type=NodeType.COMPONENTE_VID,
            label="Vigor vegetativo",
            description="Capacidad de crecimiento de la planta",
            source="Keller, M. (2015). The Science of Grapevines"
        ),
        Node(
            id="calidad_uva",
            type=NodeType.COMPONENTE_VID,
            label="Calidad de la uva",
            description="Concentración de azúcares, acidez, compuestos fenólicos",
            source="OIV. Compendium of International Methods of Wine Analysis"
        ),
        Node(
            id="produccion",
            type=NodeType.COMPONENTE_VID,
            label="Producción",
            description="Rendimiento en kg/ha",
            source="Hidalgo, L. (2002). Tratado de Viticultura General"
        ),
    ]
    
    for node in componentes:
        builder.add_node(node)

    fases = [
        Node(
            id="brotacion",
            type=NodeType.FASE_FENOLOGICA,
            label="Brotación",
            description="Inicio del ciclo vegetativo, apertura de yemas",
            source="Coombe, B.G. (1995). Growth Stages of the Grapevine"
        ),
        Node(
            id="floracion",
            type=NodeType.FASE_FENOLOGICA,
            label="Floración",
            description="Apertura de flores, fase crítica para el cuajado",
            source="Coombe, B.G. (1995). Growth Stages of the Grapevine"
        ),
        Node(
            id="envero",
            type=NodeType.FASE_FENOLOGICA,
            label="Envero",
            description="Cambio de color de las bayas, inicio de maduración",
            source="Coombe, B.G. (1995). Growth Stages of the Grapevine"
        ),
        Node(
            id="maduracion",
            type=NodeType.FASE_FENOLOGICA,
            label="Maduración",
            description="Acumulación de azúcares y desarrollo de aromas",
            source="Coombe, B.G. (1995). Growth Stages of the Grapevine"
        ),
    ]
    
    for node in fases:
        builder.add_node(node)

    acciones = [
        Node(
            id="riego",
            type=NodeType.ACCION,
            label="Riego",
            description="Aplicación de agua para compensar déficit hídrico",
            source="FAO. (2006). Evapotranspiración del cultivo"
        ),
        Node(
            id="riego_deficitario",
            type=NodeType.ACCION,
            label="Riego deficitario controlado",
            description="Riego reducido estratégicamente para mejorar calidad",
            source="Keller, M. (2015). The Science of Grapevines"
        ),
        Node(
            id="tratamiento_fungicida",
            type=NodeType.ACCION,
            label="Tratamiento fungicida",
            description="Aplicación de productos antifúngicos preventivos o curativos",
            source="MAPA. Guía de gestión integrada de plagas de la vid"
        ),
        Node(
            id="deshojado",
            type=NodeType.ACCION,
            label="Deshojado",
            description="Eliminación de hojas para mejorar aireación y exposición",
            source="Reynier, A. (2012). Manual de Viticultura"
        ),
        Node(
            id="proteccion_heladas",
            type=NodeType.ACCION,
            label="Protección contra heladas",
            description="Métodos activos o pasivos para evitar daño por frío",
            source="Hidalgo, L. (2002). Tratado de Viticultura General"
        ),
        Node(
            id="adelantar_vendimia",
            type=NodeType.ACCION,
            label="Adelantar vendimia",
            description="Cosecha anticipada para evitar pérdidas",
            source="Reynier, A. (2012). Manual de Viticultura"
        ),
        Node(
            id="aclareo_racimos",
            type=NodeType.ACCION,
            label="Aclareo de racimos",
            description="Reducción de carga para mejorar calidad",
            source="Hidalgo, L. (2002). Tratado de Viticultura General"
        ),
    ]
    
    for node in acciones:
        builder.add_node(node)
    
    relaciones_clima_riesgo = [
        Relation(
            source_id="temperatura_bajo_cero",
            target_id="helada",
            type=RelationType.PROVOCA,
            weight=0.95,
            source="Hidalgo (2002)"
        ),
        Relation(
            source_id="temperatura_baja",
            target_id="helada",
            type=RelationType.FAVORECE,
            weight=0.7,
            condition="Temperatura entre 0°C y 3°C con humedad alta",
            source="Hidalgo (2002)"
        ),
        Relation(
            source_id="temperatura_alta",
            target_id="estres_termico",
            type=RelationType.PROVOCA,
            weight=0.9,
            condition="Temperatura máxima > 35°C",
            source="Keller (2015)"
        ),
        Relation(
            source_id="precipitacion_escasa",
            target_id="estres_hidrico",
            type=RelationType.FAVORECE,
            weight=0.8,
            source="FAO (2006)"
        ),
        Relation(
            source_id="humedad_alta",
            target_id="mildiu",
            type=RelationType.FAVORECE,
            weight=0.85,
            condition="Humedad > 80% con temperatura 10-25°C",
            source="MAPA - Guía GIP Vid"
        ),
        Relation(
            source_id="humedad_alta",
            target_id="botrytis",
            type=RelationType.FAVORECE,
            weight=0.8,
            condition="Especialmente en maduración con lluvias",
            source="Reynier (2012)"
        ),
    ]
    
    for rel in relaciones_clima_riesgo:
        builder.add_relation(rel)
    
    relaciones_riesgo_efecto = [
        Relation(
            source_id="helada",
            target_id="brotes",
            type=RelationType.DAÑA,
            weight=0.95,
            condition="Especialmente en brotación",
            source="Hidalgo (2002)"
        ),
        Relation(
            source_id="helada",
            target_id="produccion",
            type=RelationType.REDUCE,
            weight=0.8,
            source="Hidalgo (2002)"
        ),
        
        Relation(
            source_id="estres_termico",
            target_id="hojas",
            type=RelationType.DAÑA,
            weight=0.7,
            condition="Quemaduras foliares con T > 40°C",
            source="Keller (2015)"
        ),
        Relation(
            source_id="estres_termico",
            target_id="calidad_uva",
            type=RelationType.REDUCE,
            weight=0.75,
            condition="Pérdida de acidez y aromas",
            source="Keller (2015)"
        ),

        Relation(
            source_id="estres_hidrico",
            target_id="vigor",
            type=RelationType.REDUCE,
            weight=0.8,
            source="FAO (2006)"
        ),
        Relation(
            source_id="estres_hidrico",
            target_id="calidad_uva",
            type=RelationType.AUMENTA,
            weight=0.6,
            condition="Estrés moderado y controlado mejora concentración",
            source="Keller (2015)"
        ),
        Relation(
            source_id="estres_hidrico",
            target_id="produccion",
            type=RelationType.REDUCE,
            weight=0.7,
            condition="Estrés severo reduce rendimiento",
            source="FAO (2006)"
        ),
        
        Relation(
            source_id="mildiu",
            target_id="hojas",
            type=RelationType.DAÑA,
            weight=0.9,
            condition="Manchas de aceite, necrosis",
            source="MAPA - Guía GIP Vid"
        ),
        Relation(
            source_id="mildiu",
            target_id="racimos",
            type=RelationType.DAÑA,
            weight=0.85,
            condition="Mildiu larvado en bayas jóvenes",
            source="MAPA - Guía GIP Vid"
        ),
        Relation(
            source_id="mildiu",
            target_id="produccion",
            type=RelationType.REDUCE,
            weight=0.8,
            source="MAPA - Guía GIP Vid"
        ),
    ]
    
    for rel in relaciones_riesgo_efecto:
        builder.add_relation(rel)
    

    relaciones_vulnerabilidad = [
        Relation(
            source_id="brotes",
            target_id="brotacion",
            type=RelationType.VULNERABLE_EN,
            weight=0.95,
            condition="Tejido joven muy sensible",
            source="Reynier (2012)"
        ),
        Relation(
            source_id="helada",
            target_id="brotacion",
            type=RelationType.VULNERABLE_EN,
            weight=0.9,
            condition="Máxima sensibilidad a heladas tardías",
            source="Hidalgo (2002)"
        ),
        Relation(
            source_id="mildiu",
            target_id="floracion",
            type=RelationType.VULNERABLE_EN,
            weight=0.85,
            condition="Infecciones primarias más dañinas",
            source="MAPA - Guía GIP Vid"
        ),
        Relation(
            source_id="estres_hidrico",
            target_id="envero",
            type=RelationType.VULNERABLE_EN,
            weight=0.7,
            condition="Déficit moderado puede ser beneficioso para calidad",
            source="Keller (2015)"
        ),
        Relation(
            source_id="botrytis",
            target_id="maduracion",
            type=RelationType.VULNERABLE_EN,
            weight=0.9,
            condition="Máxima susceptibilidad cerca de vendimia",
            source="Reynier (2012)"
        ),
    ]
    
    for rel in relaciones_vulnerabilidad:
        builder.add_relation(rel)

    relaciones_mitigacion = [
        Relation(
            source_id="proteccion_heladas",
            target_id="helada",
            type=RelationType.MITIGA,
            weight=0.8,
            condition="Aspersión, estufas, ventiladores",
            source="Hidalgo (2002)"
        ),
        
        Relation(
            source_id="riego",
            target_id="estres_hidrico",
            type=RelationType.MITIGA,
            weight=0.9,
            source="FAO (2006)"
        ),
        Relation(
            source_id="riego_deficitario",
            target_id="estres_hidrico",
            type=RelationType.MITIGA,
            weight=0.6,
            condition="Control parcial, mantiene estrés moderado beneficioso",
            source="Keller (2015)"
        ),
        Relation(
            source_id="riego_deficitario",
            target_id="calidad_uva",
            type=RelationType.AUMENTA,
            weight=0.7,
            condition="Mejora concentración en variedades tintas",
            source="Keller (2015)"
        ),
        
        Relation(
            source_id="tratamiento_fungicida",
            target_id="mildiu",
            type=RelationType.PREVIENE,
            weight=0.85,
            condition="Tratamiento preventivo antes de lluvia",
            source="MAPA - Guía GIP Vid"
        ),
        Relation(
            source_id="deshojado",
            target_id="mildiu",
            type=RelationType.INHIBE,
            weight=0.5,
            condition="Mejora aireación, reduce humedad foliar",
            source="Reynier (2012)"
        ),
        
        Relation(
            source_id="deshojado",
            target_id="botrytis",
            type=RelationType.PREVIENE,
            weight=0.7,
            condition="Mejor aireación de racimos",
            source="Reynier (2012)"
        ),
        Relation(
            source_id="adelantar_vendimia",
            target_id="botrytis",
            type=RelationType.MITIGA,
            weight=0.75,
            condition="Evita exposición prolongada a humedad",
            source="Reynier (2012)"
        ),
        
        Relation(
            source_id="riego",
            target_id="estres_termico",
            type=RelationType.MITIGA,
            weight=0.6,
            condition="Riego refrescante, mantiene turgencia",
            source="Keller (2015)"
        ),
    ]
    
    for rel in relaciones_mitigacion:
        builder.add_relation(rel)
    
    return builder


def main():
    print("Construyendo grafo de conocimiento vitícola...")
    
    builder = build_viticulture_graph()
    
    output_path = Path(__file__).parent / "knowledge_graph.json"
    builder.save(output_path)
    
    print(f"✓ Grafo guardado en {output_path}")
    print(f"  - Nodos: {len(builder.nodes)}")
    print(f"  - Relaciones: {len(builder.relations)}")
    
    from collections import Counter
    node_types = Counter(n.type.value for n in builder.nodes.values())
    rel_types = Counter(r.type.value for r in builder.relations)
    
    print("\nNodos por tipo:")
    for t, count in node_types.most_common():
        print(f"  {t}: {count}")
    
    print("\nRelaciones por tipo:")
    for t, count in rel_types.most_common():
        print(f"  {t}: {count}")


if __name__ == "__main__":
    main()
