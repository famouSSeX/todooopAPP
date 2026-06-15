from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta
from uuid import uuid4


class Zadacha(ABC):
    def __init__(self, nazvanie: str) -> None:
        self._id = str(uuid4())
        self._nazvanie = ""
        self.imya = nazvanie
        self._gotovo = False
        self._kogda_sozdali = datetime.now()

    @property
    def id(self) -> str:
        return self._id

    @property
    def imya(self) -> str:
        return self._nazvanie

    @imya.setter
    def imya(self, val: str) -> None:
        txt = val.strip()
        if not txt:
            raise ValueError("Название задачи не может быть пустым")
        if len(txt) > 200:
            raise ValueError("Название задачи не может быть длиннее 200 символов")
        self._nazvanie = txt

    @property
    def gotovo(self) -> bool:
        return self._gotovo

    @property
    def kogda_sozdana(self) -> datetime:
        return self._kogda_sozdali

    @abstractmethod
    def zavershit(self) -> None:
        pass

    @abstractmethod
    def dannie_dlya_karti(self) -> dict:
        pass

    @abstractmethod
    def prioritet(self) -> int:
        pass

    def kakoy_cvet(self) -> str:
        return "blue"

    def kakoy_tip(self) -> str:
        return "Задача"

    def stavit_gotovoy(self) -> None:
        self._gotovo = True


class ObichnayaZadacha(Zadacha):
    def zavershit(self) -> None:
        self.stavit_gotovoy()

    def dannie_dlya_karti(self) -> dict:
        return {
            "title": self.imya,
            "type": self.kakoy_tip(),
            "priority": self.prioritet(),
            "completed": self.gotovo,
            "extra": "",
        }

    def prioritet(self) -> int:
        return 1

    def kakoy_tip(self) -> str:
        return "Обычная"


class SrochnayaZadacha(ObichnayaZadacha):
    def __init__(self, nazvanie: str, srok: date | None = None) -> None:
        super().__init__(nazvanie)
        self._srok = srok or (date.today() + timedelta(days=1))

    @property
    def srok(self) -> date:
        return self._srok

    def prioritet(self) -> int:
        return 3

    def kakoy_cvet(self) -> str:
        return "red"

    def kakoy_tip(self) -> str:
        return "Срочная"

    def dannie_dlya_karti(self) -> dict:
        dannie = super().dannie_dlya_karti()
        dannie["extra"] = f"Срок: {self._srok.strftime('%d.%m.%Y')}"
        dannie["priority"] = self.prioritet()
        return dannie


class PovtorZadacha(ObichnayaZadacha):
    def __init__(self, nazvanie: str, skolko_dney: int = 7) -> None:
        super().__init__(nazvanie)
        if skolko_dney < 1:
            raise ValueError("Интервал повторения должен быть не менее 1 дня")
        self._dni = skolko_dney

    @property
    def dni(self) -> int:
        return self._dni

    def zavershit(self) -> None:
        self.stavit_gotovoy()

    def eshe_raz(self) -> "PovtorZadacha":
        return PovtorZadacha(self.imya, self._dni)

    def prioritet(self) -> int:
        return 2

    def kakoy_cvet(self) -> str:
        return "green"

    def kakoy_tip(self) -> str:
        return "Повторяющаяся"

    def dannie_dlya_karti(self) -> dict:
        dannie = super().dannie_dlya_karti()
        dannie["extra"] = f"Каждые {self._dni} дн."
        dannie["priority"] = self.prioritet()
        return dannie


class SpisokZadach:
    def __init__(self) -> None:
        self._zadachi: list[Zadacha] = []

    def dobavit(self, zadacha: Zadacha) -> None:
        if not isinstance(zadacha, Zadacha):
            raise TypeError("Можно добавлять только Zadacha")
        self._zadachi.append(zadacha)

    def udalit(self, zadacha_id: str) -> None:
        self._zadachi = [z for z in self._zadachi if z.id != zadacha_id]

    def vse(self) -> list[Zadacha]:
        return list(self._zadachi)

    def nayti(self, zadacha_id: str) -> Zadacha | None:
        for z in self._zadachi:
            if z.id == zadacha_id:
                return z
        return None

    def otmetit_gotovoy(self, zadacha_id: str) -> None:
        z = self.nayti(zadacha_id)
        if z is None:
            raise ValueError(f"Задача с id={zadacha_id} не найдена")
        z.zavershit()
        if isinstance(z, PovtorZadacha):
            self.udalit(zadacha_id)
            self.dobavit(z.eshe_raz())
