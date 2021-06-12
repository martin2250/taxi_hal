# TAXI HAL

WIP

```bash
inotifywait -me close_write --format %w%f src/taxi_hal/* | while read FILE; scp "$FILE" "taxi114:/home/root/martin/taxi_hal/$FILE"; end
```