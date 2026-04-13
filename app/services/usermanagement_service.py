from .db import execute_query, execute_query_one
from uuid import UUID
import json
from typing import List, Dict, Optional

async def create_user_assignments(user_ids: List[UUID], course_ids: List[UUID]) -> List[UUID]:
    """
    Crea múltiples asignaciones evitando duplicados de forma eficiente.
    Solo devuelve los IDs de las asignaciones que fueron CREADAS en esta llamada.
    """
    query = """
    INSERT INTO conversaconfig.user_course_assignments (user_id, course_id)
    SELECT u.id, c.id
    FROM unnest($1::uuid[]) AS u(id)
    CROSS JOIN unnest($2::uuid[]) AS c(id)
    ON CONFLICT (user_id, course_id) DO NOTHING
    RETURNING assignment_id
    """
    
    # Ejecutamos la consulta
    results = await execute_query(query, user_ids, course_ids)
    
    if not results:
        return []
        
    # Importante: RETURNING solo devolverá filas que realmente se insertaron.
    # Si una combinación ya existía, ON CONFLICT la ignora y no aparece aquí.
    return [row["assignment_id"] for row in results]


async def delete_user_assignments(user_ids: List[UUID], course_ids: List[UUID]) -> int:
    """
    Elimina todas las combinaciones de la tabla que coincidan con los IDs proporcionados.
    Retorna el número de filas eliminadas.
    """
    query = """
    DELETE FROM conversaconfig.user_course_assignments
    WHERE user_id = ANY($1::uuid[])
      AND course_id = ANY($2::uuid[])
    RETURNING assignment_id
    """
    
    # Ejecutamos la consulta y obtenemos todos los registros eliminados
    results = await execute_query(query, user_ids, course_ids)
    
    # Retornamos la cantidad de elementos eliminados
    return len(results) if results else 0


async def create_journey_assignments_bulk(user_ids: List[UUID], journey_ids: List[UUID]) -> List[UUID]:
    """
    Genera el producto cartesiano entre users y journeys.
    Inserta solo los que no existen gracias a ON CONFLICT DO NOTHING.
    """
    query = """
    INSERT INTO conversaconfig.user_journeys_assigments (user_id, journey_id)
    SELECT u.id, j.id
    FROM unnest($1::uuid[]) AS u(id)
    CROSS JOIN unnest($2::uuid[]) AS j(id)
    ON CONFLICT (user_id, journey_id) DO NOTHING
    RETURNING user_journey_id
    """
    
    results = await execute_query(query, user_ids, journey_ids)
    
    if not results:
        return []
        
    return [row["user_journey_id"] for row in results]


async def delete_journey_assignments_bulk(user_ids: List[UUID], journey_ids: List[UUID]) -> int:
    """
    Elimina todas las combinaciones que existan en la tabla 
    cuyos user_id y journey_id pertenezcan a las listas proporcionadas.
    """
    query = """
    DELETE FROM conversaconfig.user_journeys_assigments
    WHERE user_id = ANY($1::uuid[])
      AND journey_id = ANY($2::uuid[])
    RETURNING user_journey_id
    """
    
    results = await execute_query(query, user_ids, journey_ids)
    
    return len(results) if results else 0



async def create_journey_courses_bulk(
    journey_ids: List[UUID], 
    course_ids: List[UUID],
    is_mandatory: bool = True,
    milestone_id: UUID = None
) -> List[UUID]:
    """
    Inserta cursos en journeys usando el índice del array como display_order.
    Requiere que exista un UNIQUE(journey_id, course_id) en la base de datos.
    """
    # Usamos WITH ORDINALITY para obtener el índice de cada curso en el array (empieza en 1)
    query = """
    INSERT INTO conversaconfig.journey_courses (journey_id, course_id, display_order, is_mandatory, milestone_id)
    SELECT j.id, c.id, c.ord, $3, $4
    FROM unnest($1::uuid[]) AS j(id)
    CROSS JOIN unnest($2::uuid[]) WITH ORDINALITY AS c(id, ord)
    ON CONFLICT (journey_id, course_id) DO NOTHING
    RETURNING journey_course_id
    """
    
    # IMPORTANTE: Asegúrate de pasar los parámetros en el orden correcto ($1, $2, $3, $4)
    results = await execute_query(query, journey_ids, course_ids, is_mandatory, milestone_id)
    
    if not results:
        return []
        
    return [row["journey_course_id"] for row in results]


async def delete_journey_courses_bulk(journey_ids: List[UUID], course_ids: List[UUID]) -> int:
    """
    Elimina los cursos de los journeys especificados.
    """
    query = """
    DELETE FROM conversaconfig.journey_courses
    WHERE journey_id = ANY($1::uuid[])
      AND course_id = ANY($2::uuid[])
    RETURNING journey_course_id
    """
    
    results = await execute_query(query, journey_ids, course_ids)
    
    return len(results) if results else 0