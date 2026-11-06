# NOTHING / NIRI

Монохромный стартовый rice для Arch Linux + Niri: графитовый фон,
белые контуры, скругления 18 px, панель из отдельных капсул.
Без цветовых акцентов; терминальная палитра тоже чёрно-белая.

## Состав

- Niri — окна, раскладки US/RU, горячие клавиши.
- Waybar — рабочие столы, часы, сеть, звук, батарея, трей.
- Fuzzel — приложения; Kitty — основной терминал; Foot — запасной; Mako — уведомления.
- Swaylock — ручная блокировка. Автоблокировка пока не настроена.

Часы используют `Ndot 57`, если он уже установлен, иначе JetBrains Mono.
Шрифт Nothing в репозиторий не включён. Обои пока однотонные.
Это стартовый конфиг, а не готовая копия оболочки Nothing OS.

## Перенос на ноутбук с Arch

Разработка ведётся на macOS; Linux-сессию здесь проверить нельзя.
На целевом ноутбуке сначала сохрани текущие dotfiles. В присланном конфиге Serpentinum
запускается строкой `spawn-at-startup "serpantinumd" "start"`. В новом конфиге
этой строки нет. После выхода из старой сессии проверь, не остаётся ли
оболочка запущенной через отдельную службу или XDG autostart. Удалять её не нужно.
Гритер и настройки менеджера входа этот проект не меняет.

Зависимости на Arch:

```sh
sudo pacman -S --needed niri waybar fuzzel kitty foot mako swaybg swaylock \
  ttf-jetbrains-mono pipewire wireplumber pavucontrol brightnessctl \
  xdg-desktop-portal-gnome xdg-desktop-portal-gtk \
  wl-clipboard cliphist polkit-gnome playerctl firefox nautilus
```

Команда предполагает уже работающие звук, сеть и Niri. Она не настраивает
драйверы, службы, polkit, Bluetooth и менеджер входа.

Скопируй репозиторий на Arch и из его каталога выполни:

```sh
niri validate -c config/niri/config.kdl
bash scripts/install.sh --replace
niri validate
```

`--replace` переносит существующие каталоги `niri`, `waybar`, `fuzzel`,
`foot`, `mako`, `swaylock`, `kitty` в резервную копию в
`${XDG_STATE_HOME:-~/.local/state}/nothing-rice/backups/`.
Без флага установка прекращается при обнаружении существующего конфига.
Niri может применить конфиг сразу: запускай установку из TTY после выхода
из графической сессии. При ошибке валидации верни каталог `niri` из копии,
прежде чем входить в сессию. Для полного отката верни все семь каталогов;
новые предварительно перемести в отдельную папку.

## Настройки твоего ноутбука

Из присланного конфига перенесены `eDP-1`, 1920×1200 @ 60.001 Hz,
масштаб 1.5, VRR по запросу, фокус за мышью, рабочие столы `sysinfo`
и `monitor`, курсор Bibata-Modern-Ice, qt6ct, агент polkit и история буфера.
Bibata, qt6ct и EasyEffects предполагаются уже установленными, как в прежней сессии.
Запуск существующей службы EasyEffects сохранён без повторного `enable`.
Правила Noctalia, общая прозрачность 75% и blur не перенесены.
Новые окна, как раньше, занимают полную ширину; Mod+R меняет ширину.

Все активные горячие клавиши из присланного файла сохранены:

| Клавиши | Действие |
| --- | --- |
| Mod+T | Kitty |
| Mod+D | Fuzzel |
| Mod+B / Mod+E | Firefox / Nautilus |
| Mod+Space | Обзор |
| Mod+стрелки или H/J/K/L | Фокус |
| Mod+Ctrl+стрелки | Перемещение окон / колонок |
| Mod+Shift+стрелки | Фокус на другом мониторе |
| Mod+1…9 | Рабочий стол |
| Mod+R | Ширина колонки |
| Mod+F / Mod+Shift+F | Развернуть колонку / полный экран |
| Super+Alt+L | Блокировка |
| Mod+Escape | Переключить перехват горячих клавиш |
| Mod+Shift+E | Выход с подтверждением Niri |

Alt+Shift переключает US/RU, Caps Lock работает как Ctrl, правый Alt — Compose.

## Источники

- [Конфигурация Niri](https://niri-wm.github.io/niri/Configuration:-Introduction)
- [Эталонный конфиг Niri](https://github.com/niri-wm/niri/blob/main/resources/default-config.kdl)
- [Модуль рабочих столов Waybar](https://github.com/Alexays/Waybar/blob/master/man/waybar-niri-workspaces.5.scd)
