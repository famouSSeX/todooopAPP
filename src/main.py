import sys
from datetime import date, timedelta
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parent
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

import flet as ft

from models import ObichnayaZadacha, PovtorZadacha, SrochnayaZadacha, SpisokZadach, Zadacha


def sdelat_iz_formy(vvod: dict) -> Zadacha:
    imya = vvod["title"]
    tip = vvod["type"]

    if tip == "urgent":
        srok = vvod.get("deadline") or (date.today() + timedelta(days=1))
        return SrochnayaZadacha(imya, srok)
    if tip == "recurring":
        dni = int(vvod.get("interval_days", 7))
        return PovtorZadacha(imya, dni)
    return ObichnayaZadacha(imya)


def narisovat_kartochku(zadacha: Zadacha, kogda_gotovo, kogda_udalit) -> ft.Card:
    dannie = zadacha.dannie_dlya_karti()
    cveta = {
        "blue": ft.Colors.BLUE,
        "red": ft.Colors.RED,
        "green": ft.Colors.GREEN,
    }
    cvet = cveta.get(zadacha.kakoy_cvet(), ft.Colors.BLUE)

    stil = ft.TextStyle(
        decoration=ft.TextDecoration.LINE_THROUGH if dannie["completed"] else None,
    )

    return ft.Card(
        content=ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(width=4, height=48, bgcolor=cvet, border_radius=2),
                    ft.Column(
                        controls=[
                            ft.Text(dannie["title"], style=stil, weight=ft.FontWeight.W_500),
                            ft.Text(
                                f"{dannie['type']} · приоритет {dannie['priority']}",
                                size=12,
                                color=ft.Colors.GREY_700,
                            ),
                            ft.Text(dannie["extra"], size=12, color=ft.Colors.GREY_600)
                            if dannie["extra"]
                            else ft.Container(),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
                        tooltip="Выполнить",
                        on_click=lambda e, i=zadacha.id: kogda_gotovo(i),
                        disabled=dannie["completed"],
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        tooltip="Удалить",
                        icon_color=ft.Colors.RED_400,
                        on_click=lambda e, i=zadacha.id: kogda_udalit(i),
                    ),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            padding=12,
        ),
    )


class OknoDobavleniya:
    def __init__(self, pg: ft.Page, esli_dobavili) -> None:
        self.pg = pg
        self.esli_dobavili = esli_dobavili

        self.pole_imya = ft.TextField(label="Название", autofocus=True, max_length=200)
        self.vybor_tipa = ft.Dropdown(
            label="Тип задачи",
            options=[
                ft.DropdownOption(key="simple", text="Обычная"),
                ft.DropdownOption(key="urgent", text="Срочная"),
                ft.DropdownOption(key="recurring", text="Повторяющаяся"),
            ],
            value="simple",
            on_select=self.kogda_smenil_tip,
        )
        self.pole_srok = ft.TextField(
            label="Срок (ГГГГ-ММ-ДД)",
            visible=False,
            value=(date.today() + timedelta(days=1)).isoformat(),
        )
        self.pole_dni = ft.TextField(
            label="Интервал (дней)",
            visible=False,
            value="7",
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        self.tekst_oshibki = ft.Text("", color=ft.Colors.RED_400, size=12, visible=False)

        self.okno = ft.AlertDialog(
            modal=True,
            title=ft.Text("Новая задача"),
            content=ft.Column(
                controls=[
                    self.pole_imya,
                    self.vybor_tipa,
                    self.pole_srok,
                    self.pole_dni,
                    self.tekst_oshibki,
                ],
                tight=True,
                width=360,
            ),
            actions=[
                ft.TextButton("Отмена", on_click=self.zakryt_okno),
                ft.FilledButton("Добавить", on_click=self.nazhat_dobavit),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def pokazat_oshibku_v_okne(self, tekst: str) -> None:
        self.tekst_oshibki.value = tekst
        self.tekst_oshibki.visible = True
        self.okno.update()

    def skryt_oshibku(self) -> None:
        self.tekst_oshibki.value = ""
        self.tekst_oshibki.visible = False

    def kogda_smenil_tip(self, e) -> None:
        tip = self.vybor_tipa.value
        self.pole_srok.visible = tip == "urgent"
        self.pole_dni.visible = tip == "recurring"
        self.skryt_oshibku()
        self.okno.update()

    def pokazat(self) -> None:
        self.pole_imya.value = ""
        self.vybor_tipa.value = "simple"
        self.pole_srok.visible = False
        self.pole_dni.visible = False
        self.skryt_oshibku()
        self.pg.show_dialog(self.okno)

    def zakryt_okno(self, e) -> None:
        self.pg.pop_dialog()

    def nazhat_dobavit(self, e) -> None:
        try:
            vvod: dict = {
                "title": self.pole_imya.value or "",
                "type": self.vybor_tipa.value,
            }
            if vvod["type"] == "urgent":
                vvod["deadline"] = date.fromisoformat(self.pole_srok.value)
            if vvod["type"] == "recurring":
                vvod["interval_days"] = int(self.pole_dni.value or "7")
            zadacha = sdelat_iz_formy(vvod)
            self.zakryt_okno(e)
            self.esli_dobavili(zadacha)
        except (ValueError, TypeError) as err:
            self.pokazat_oshibku_v_okne(str(err))


class Glavnaya:
    def __init__(self, pg: ft.Page) -> None:
        self.pg = pg
        self.spisok = SpisokZadach()
        self.scroll = ft.ListView(expand=True, spacing=8)
        self.okno = OknoDobavleniya(pg, self.kogda_dobavili)

        self.ekran = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("Список задач", size=24, weight=ft.FontWeight.BOLD),
                        ft.IconButton(
                            icon=ft.Icons.ADD_CIRCLE,
                            icon_size=32,
                            tooltip="Добавить задачу",
                            on_click=lambda e: self.okno.pokazat(),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                self.scroll,
            ],
            expand=True,
            spacing=8,
        )

    def pokazat_oshibku(self, tekst: str) -> None:
        self.pg.show_dialog(ft.SnackBar(content=ft.Text(tekst)))

    def kogda_dobavili(self, zadacha: Zadacha) -> None:
        try:
            self.spisok.dobavit(zadacha)
            self.pererisovat_spisok()
        except (ValueError, TypeError) as err:
            self.pokazat_oshibku(str(err))

    def kogda_gotovo(self, zadacha_id: str) -> None:
        try:
            self.spisok.otmetit_gotovoy(zadacha_id)
            self.pererisovat_spisok()
        except ValueError as err:
            self.pokazat_oshibku(str(err))

    def kogda_udalili(self, zadacha_id: str) -> None:
        self.spisok.udalit(zadacha_id)
        self.pererisovat_spisok()

    def pererisovat_spisok(self) -> None:
        vse = sorted(
            self.spisok.vse(),
            key=lambda z: (-z.prioritet(), z.kogda_sozdana),
        )
        self.scroll.controls = [
            narisovat_kartochku(z, self.kogda_gotovo, self.kogda_udalili) for z in vse
        ]
        self.scroll.update()


def zapusk(pg: ft.Page) -> None:
    pg.title = "Список задач"
    pg.theme_mode = ft.ThemeMode.LIGHT
    pg.padding = 16
    pg.window.width = 480
    pg.window.height = 720

    ekran = Glavnaya(pg)
    pg.add(
        ft.Container(
            content=ekran.ekran,
            expand=True,
        )
    )
    pg.update()


main = zapusk


if __name__ == "__main__":
    ft.run(zapusk, assets_dir=str(_APP_DIR / "assets"))
