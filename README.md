# Задание за проект относно РАГИС курс 2024г.

ОКС Бакалавър и ОКС Магистър

## Структура:

1. Разписване на заданието за задачата в документ, както и обосновка защо студента иска да разработи това;
2. Събиране и обработка на данни

- търсене на данни, изчистване на данни, георефериране на данни от csv формати; или изчертаване на данни по предварително задание от примерните проекти;

3. Анализи

- Писане на пространствени анализи, които следва да решат задачата - SQL и Python, документиране на кода и на резултатите от анализите в GitHub;

4. Онлайн карта
5. Изводи

- Разписване на изводи в документ

## Очакван резултат:

- поне 1 документ с описание на задачата, методология и изводи
- GitHub документация

## Задача: Изчисление на пешеходен индекс за София – Звезди

Целта е да се изчисли кои, колко и на какво разстояние са точките на интерес, до които всяка сграда има пешеходен достъп. Това се обобщава в пешеходен индекс, за обслужеността от функции на една сграда. Изчислението трябва да бъде написано на python или поетапно чрез SQL към базата.

### Локация: София (пилотно да се тества с извадки от данни). 3 квартала, по които да се работи и да се сравняват. Избрани квартали: Младост, Дианабад, Лозенец и Витошa като лошо обслужен квартал;

### Входни данни:

- центроиди (точки) на жилищни сгради - може би по добре с входовете на сградите за да сме по- точни
- Пешеходна мрежа
- точки на интерес (училища, детски градини, спортни обекти ...)
- json за точкуване на всяка от точките на интерес