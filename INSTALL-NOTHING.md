# Установка Nothing / Niri

[Описание проекта](README.ru.md) · [English quick start](README.md#install)

Для существующей установки **Arch Linux + Niri**. Hyprland и Serpentinum не требуются. Сначала убедись, что Niri, интернет и звук работают, а файл `~/.config/niri/config.kdl` существует. Если задан `XDG_CONFIG_HOME`, конфиг должен находиться в нём.

Используй **`scripts/install-nothing.py`**. Скрипты `install.sh` и `style-serpantinum.py` относятся к предыдущим вариантам оформления.

## 1. Зависимости

В терминале Arch выполни одной строкой:

```bash
sudo pacman -Syu --needed git quickshell python fontconfig ttf-jetbrains-mono-nerd curl cava brightnessctl swaylock pavucontrol network-manager-applet blueman
```

Предполагаются уже работающие Niri, PipeWire и системные службы сети/Bluetooth. Для выбора CPU-профилей дополнительно нужен работающий power-profiles-daemon.

## 2. Скачать проект

```bash
git clone https://github.com/dashatuchka/nothing-os-ricing.git
cd nothing-os-ricing
```

Либо скачай **Code → Download ZIP** на GitHub, распакуй архив и открой полученную папку в терминале. В ней должна работать команда:

```bash
ls scripts/install-nothing.py
```

Дальнейшие команды запускаются из этой папки. Запомни её путь: он понадобится после перехода в TTY.

## 3. Выбрать шрифт

**Doto** включён в репозиторий и используется по умолчанию — это шрифт оригинального Glyph. Space Grotesk и Space Mono для обычного текста тоже включены.

Для **Ndot 57** есть два варианта:

- Добавить `--download-ndot` к командам подготовки и установки. Файл скачивается из стороннего репозитория, проверяется по SHA-256 и имени семейства.
- Передать уже имеющийся файл через `--dot-font "$HOME/Downloads/Ndot57-Regular.otf"` вместо `--download-ndot`.

Сам Ndot в Git не хранится. Указывай выбранный параметр на обоих этапах: подготовка и применение — разные операции.

## 4. Подготовить без установки

С Doto:

```bash
python3 scripts/install-nothing.py --output "/tmp/nothing-preview-$(date +%s)"
```

Или с загрузкой Ndot 57:

```bash
python3 scripts/install-nothing.py --download-ndot --output "/tmp/nothing-preview-$(date +%s)"
```

Должны появиться `config is valid` и `Prepared in ...`. Это проверка и подготовка файлов, **она ещё не устанавливает оболочку**. При ошибке не переходи к применению: сохрани полный вывод.

Установщик ожидает один блок `binds`, однострочный бинд `Mod+D` и свободные `Mod+A`, `Mod+N`, `Mod+Shift+D`. При неоднозначном конфиге он останавливается, не заменяя его.

## 5. Установить из TTY

Сохрани документы и выйди из графической сессии Niri. Перейди в TTY через `Ctrl+Alt+F3`, войди под своим пользователем и перейди в папку проекта, например:

```bash
cd ~/nothing-os-ricing
```

Для Doto:

```bash
python3 scripts/install-nothing.py --apply
```

Для Ndot 57 выполни вместо этой команды:

```bash
python3 scripts/install-nothing.py --apply --download-ndot
```

Либо используй свой файл:

```bash
python3 scripts/install-nothing.py --apply --dot-font "$HOME/Downloads/Ndot57-Regular.otf"
```

Запускай установщик **без sudo**. После успешной установки появятся:

- `Installed independent Nothing shell`;
- путь резервной копии;
- готовая команда `Rollback:`.

**Сохрани эту команду отката.** Затем:

```bash
niri validate
```

Если конфиг валиден:

```bash
sudo reboot
```

Войди в свою обычную сессию Niri через прежний гритер.

## Что устанавливается

| Путь | Содержимое |
| --- | --- |
| `~/.config/quickshell/nothing/` | Новая оболочка, её компоненты и launcher |
| `~/.config/nothing-niri/settings.json` | Координаты города и параметры файла шрифта |
| `~/.local/state/nothing-niri/glyph.json` | Состав виджетов, тема, шрифт и состояние интерфейса |
| `~/.local/state/nothing-rice/full-shell-backups/` | Резервные копии заменённых файлов |

Пути учитывают `XDG_CONFIG_HOME` и `XDG_STATE_HOME`.

В текущем конфиге Niri заменяются прямые запуски Serpentinum, Waybar, Mako, swaybg и других qs-оболочек. Новый фон рисует сама оболочка. Меняются `Mod+D` и три бинда панелей; остальные настройки Niri сохраняются.

Программы, прежние обои и гритер не удаляются. Исходники установленного Serpentinum не патчатся. Отдельные службы systemd user и XDG autostart не отключаются автоматически.

## Управление

| Клавиши | Действие |
| --- | --- |
| `Super+D` | Лаунчер приложений |
| `Super+A` | Звук, яркость, виджеты, тема, шрифт, DND и уведомления |
| `Super+N` | Календарь и орбитальный прогноз |
| `Super+Shift+D` | Нижний дашборд |

`Super` — обычно клавиша Windows. Часы и статусы верхнего бара тоже открывают панели. Терминал, обзор и блокировка используют прежние бинды твоего конфига. Кнопка блокировки в меню питания запускает Swaylock.

## Погода

Если Serpentinum раньше был настроен, установщик может перенести город из его настроек. Иначе отредактируй поле `location` в файле:

```bash
nano "${XDG_CONFIG_HOME:-$HOME/.config}/nothing-niri/settings.json"
```

Например, для Berlin:

```json
"location": {
  "latitude": 52.52,
  "longitude": 13.40,
  "city": "Berlin",
  "timezone": "Europe/Berlin"
}
```

Укажи координаты своего города. Не удаляй остальные поля файла, особенно `dotFontPath` и `dotFontFamily`. После сохранения выйди из сессии и войди снова.

Данные загружаются из Open-Meteo. Без координат оболочка пробует определить место по IP. Музыка берётся из MPRIS-плееров; отдельная авторизация Spotify внутри оболочки не нужна.

## Откат

Выйди из Niri и перейди в TTY. Выполни сохранённую команду, например:

```bash
python3 scripts/install-nothing.py --restore /полный/путь/к/резервной-копии
```

Подставь реальный путь из вывода установки. Затем:

```bash
niri validate
sudo reboot
```

Откат возвращает предыдущий конфиг Niri и состояние заменённых путей. Текущие файлы перед восстановлением тоже сохраняются.

## Обновления

Установленные файлы — копии, поэтому `git pull` не меняет работающий интерфейс. Повторный `--apply` поверх уже настроенной оболочки намеренно запрещён. Автоматического обновления пока нет: восстанови предыдущую сессию перед новой установкой или используй отдельную инструкцию конкретного обновления.

## Если оформление не изменилось

Убедись, что выполнен `--apply`, а не только подготовка `--output`:

```bash
ls -l "${XDG_CONFIG_HOME:-$HOME/.config}/quickshell/nothing/launch.py"
```

Если файла нет, сохрани вывод установщика: установка не записала оболочку в ожидаемый каталог. Если файл есть, запусти из терминала Niri:

```bash
python3 "${XDG_CONFIG_HOME:-$HOME/.config}/quickshell/nothing/launch.py"
```

Для диагностики центра управления:

```bash
qs -p "${XDG_CONFIG_HOME:-$HOME/.config}/quickshell/nothing" ipc call nothing quick
```

Если одновременно видны две панели, проверь службы и XDG autostart прежней оболочки. Для помощи создай [issue](https://github.com/dashatuchka/nothing-os-ricing/issues) с полным выводом и версиями Niri/Quickshell. Не публикуй личные координаты и секреты.

## Проверки

Оболочка используется на Arch + Niri. Дополнительно запущена во вложенном Niri 26.04 с Quickshell 0.3.2 и Qt 6.12: проверены домашний экран, календарь с Open-Meteo, центр управления, лаунчер, Ndot 57 и подготовка установщика через настоящий `niri validate`.

Пять автоматических проверок покрывают события Niri, миграцию конфига, сохранение биндов, монохромную палитру, применение и откат. Аппаратные функции зависят от служб ноутбука; поддержка всех устройств и других дистрибутивов не заявляется.

[Исходные компоненты и лицензии](config/quickshell/nothing/UPSTREAM.md).
