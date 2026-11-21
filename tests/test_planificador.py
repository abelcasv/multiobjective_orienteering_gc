import json
import unittest

from src.core.problem import GAConfig
from src.pipeline import scenario_output_dir
from src.planificador import cargar_categorias, categorias_disponibles, optimizar_ruta

RAPIDO = GAConfig(population_size=40, generations=40)
SC = "santa_catalina"
LOPESAN = "lopesan_villa_del_conde"
TODAS = categorias_disponibles(SC)


def _todas_las_rutas(resultado):
    """Frente completo más las 3 rutas recomendadas."""
    rutas = list(resultado.frente) + [resultado.express, resultado.equilibrada, resultado.exhaustiva]
    return [ind for ind in rutas if ind is not None]


class TestOptimizarRuta(unittest.TestCase):
    def test_excluidos_no_aparecen_en_ninguna_ruta(self) -> None:
        excluidos = ["Bufadero de la Garita", "Tufia (Poblado y Playa)", "Arucas (Iglesia)"]
        res = optimizar_ruta(SC, 480, TODAS, excluidos, config=RAPIDO)
        self.assertFalse(res.vacio)
        for ind in _todas_las_rutas(res):
            for nombre in excluidos:
                self.assertNotIn(nombre, res.paradas(ind))

    def test_obligatorio_aparece_en_todas_las_rutas(self) -> None:
        for escenario, obligatorio in ((SC, "Playa de las Canteras"), (LOPESAN, "Roque Nublo")):
            with self.subTest(escenario=escenario):
                res = optimizar_ruta(escenario, 480, TODAS, [], obligatorio=obligatorio, config=RAPIDO)
                self.assertFalse(res.vacio)
                for ind in _todas_las_rutas(res):
                    self.assertIn(obligatorio, res.paradas(ind))

    def test_ninguna_ruta_supera_t_max(self) -> None:
        for t_max in (180, 300, 480):
            with self.subTest(t_max=t_max):
                res = optimizar_ruta(LOPESAN, t_max, TODAS, ["Barranco de Fataga"],
                                     obligatorio="Dunas de Maspalomas", config=RAPIDO)
                self.assertFalse(res.vacio)
                for ind in _todas_las_rutas(res):
                    self.assertLessEqual(ind.total_time, t_max)
                    self.assertEqual(ind.violation, 0.0)

    def test_solo_aparecen_pois_de_las_categorias_marcadas(self) -> None:
        cats = cargar_categorias(SC)
        res = optimizar_ruta(SC, 480, ["Playa y costa"], [], config=RAPIDO)
        self.assertFalse(res.vacio)
        for ind in _todas_las_rutas(res):
            for nombre in res.paradas(ind):
                self.assertIn("Playa y costa", cats[nombre])

    def test_obligatorio_se_admite_aunque_su_categoria_no_este_marcada(self) -> None:
        res = optimizar_ruta(SC, 480, ["Playa y costa"], [], obligatorio="Roque Nublo", config=RAPIDO)
        self.assertFalse(res.vacio)
        for ind in _todas_las_rutas(res):
            self.assertIn("Roque Nublo", res.paradas(ind))

    def test_categorias_vacias_da_resultado_vacio_con_motivo(self) -> None:
        res = optimizar_ruta(SC, 480, [], [], config=RAPIDO)
        self.assertTrue(res.vacio)
        self.assertIsNone(res.express)
        self.assertIn("categoría", res.motivo)

    def test_obligatorio_descartado_da_resultado_vacio_con_motivo(self) -> None:
        res = optimizar_ruta(SC, 480, TODAS, ["Roque Nublo"], obligatorio="Roque Nublo", config=RAPIDO)
        self.assertTrue(res.vacio)
        self.assertIn("has descartado la visita obligatoria", res.motivo.lower())

    def test_obligatorio_que_no_cabe_da_resultado_vacio_con_motivo(self) -> None:
        # Desde Santa Catalina, ir al Roque Nublo, visitarlo y volver lleva unos 230 min.
        res = optimizar_ruta(SC, 200, TODAS, [], obligatorio="Roque Nublo", config=RAPIDO)
        self.assertTrue(res.vacio)
        self.assertIn("no cabe", res.motivo)
        self.assertEqual(res.a_dict()["opciones_recomendadas"], {})

    def test_sin_lugares_permitidos_da_resultado_vacio_con_motivo(self) -> None:
        playas = [n for n, c in cargar_categorias(SC).items() if "Playa y costa" in c]
        res = optimizar_ruta(SC, 480, ["Playa y costa"], playas, config=RAPIDO)
        self.assertTrue(res.vacio)
        self.assertIn("ningún lugar", res.motivo)

    def test_nombres_desconocidos_lanzan_value_error(self) -> None:
        with self.assertRaises(ValueError):
            optimizar_ruta("hotel_inventado", 480, TODAS, [])
        with self.assertRaises(ValueError):
            optimizar_ruta(SC, 480, ["Gastronomía"], [])
        with self.assertRaises(ValueError):
            optimizar_ruta(SC, 480, TODAS, ["Teide"])
        with self.assertRaises(ValueError):
            optimizar_ruta(SC, 480, TODAS, [], obligatorio="Hotel Santa Catalina (Las Palmas)")

    def test_sin_restricciones_reproduce_main(self) -> None:
        """Con todas las categorías y nada descartado sale el mismo frente que main.py."""
        res = optimizar_ruta(SC, 480, TODAS, [])
        with open(scenario_output_dir(SC) / "rutas_pareto.json", encoding="utf-8") as f:
            esperado = json.load(f)
        obtenido = res.a_dict()
        self.assertEqual(obtenido["frente_pareto_completo"], esperado["frente_pareto_completo"])
        for clave in ("express", "equilibrada", "exhaustiva"):
            self.assertEqual(obtenido["opciones_recomendadas"][clave],
                             esperado["opciones_recomendadas"][clave])


if __name__ == "__main__":
    unittest.main()
