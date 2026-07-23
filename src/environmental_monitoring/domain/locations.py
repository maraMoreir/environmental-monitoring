"""Reference data: Brazil's 27 states (26 states + Federal District) and
their capital cities' coordinates.

Pure reference data, no I/O — used by the OpenWeatherMap adapter (needs
lat/lon to call the API) and by the dashboard/API (need human-readable
labels for sensor IDs), which is why it lives in `domain/` rather than
`infrastructure/`: both of those layers are allowed to depend on `domain/`,
but the dashboard must never depend on `infrastructure/` directly.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BrazilLocation:
    state_code: str
    state_name: str
    capital: str
    latitude: float
    longitude: float

    @property
    def sensor_id(self) -> str:
        return f"br-{self.state_code.lower()}"

    @property
    def label(self) -> str:
        return f"{self.capital}, {self.state_code}"


BRAZIL_STATE_CAPITALS: tuple[BrazilLocation, ...] = (
    BrazilLocation("AC", "Acre", "Rio Branco", -9.97, -67.81),
    BrazilLocation("AL", "Alagoas", "Maceió", -9.65, -35.70),
    BrazilLocation("AP", "Amapá", "Macapá", 0.03, -51.07),
    BrazilLocation("AM", "Amazonas", "Manaus", -3.10, -60.02),
    BrazilLocation("BA", "Bahia", "Salvador", -12.97, -38.51),
    BrazilLocation("CE", "Ceará", "Fortaleza", -3.72, -38.54),
    BrazilLocation("DF", "Distrito Federal", "Brasília", -15.79, -47.88),
    BrazilLocation("ES", "Espírito Santo", "Vitória", -20.32, -40.34),
    BrazilLocation("GO", "Goiás", "Goiânia", -16.68, -49.25),
    BrazilLocation("MA", "Maranhão", "São Luís", -2.53, -44.30),
    BrazilLocation("MT", "Mato Grosso", "Cuiabá", -15.60, -56.10),
    BrazilLocation("MS", "Mato Grosso do Sul", "Campo Grande", -20.44, -54.65),
    BrazilLocation("MG", "Minas Gerais", "Belo Horizonte", -19.92, -43.94),
    BrazilLocation("PA", "Pará", "Belém", -1.46, -48.50),
    BrazilLocation("PB", "Paraíba", "João Pessoa", -7.12, -34.86),
    BrazilLocation("PR", "Paraná", "Curitiba", -25.43, -49.27),
    BrazilLocation("PE", "Pernambuco", "Recife", -8.05, -34.90),
    BrazilLocation("PI", "Piauí", "Teresina", -5.09, -42.80),
    BrazilLocation("RJ", "Rio de Janeiro", "Rio de Janeiro", -22.91, -43.17),
    BrazilLocation("RN", "Rio Grande do Norte", "Natal", -5.79, -35.21),
    BrazilLocation("RS", "Rio Grande do Sul", "Porto Alegre", -30.03, -51.23),
    BrazilLocation("RO", "Rondônia", "Porto Velho", -8.76, -63.90),
    BrazilLocation("RR", "Roraima", "Boa Vista", 2.82, -60.67),
    BrazilLocation("SC", "Santa Catarina", "Florianópolis", -27.60, -48.55),
    BrazilLocation("SP", "São Paulo", "São Paulo", -23.55, -46.63),
    BrazilLocation("SE", "Sergipe", "Aracaju", -10.91, -37.07),
    BrazilLocation("TO", "Tocantins", "Palmas", -10.25, -48.32),
)
