def validate(config):
    if not isinstance(config.AP_PASSWORD, str) or not 8 <= len(config.AP_PASSWORD) <= 63:
        raise ValueError("AP_PASSWORD must be 8-63 characters")
    if not isinstance(config.AP_SSID, str) or not 1 <= len(config.AP_SSID.encode()) <= 32:
        raise ValueError("AP_SSID must be 1-32 UTF-8 bytes")
    for name in ("TELNET_PORT", "MAX_CLIENTS", "IDLE_TIMEOUT", "MAX_LINE_LENGTH"):
        value = getattr(config, name)
        if type(value) is not int or value <= 0:
            raise ValueError(name + " must be a positive integer")
    if config.TELNET_PORT > 65535:
        raise ValueError("TELNET_PORT must be at most 65535")
    for name in ("SAVE_INTERVAL", "MAX_USERS", "MAX_ROOMS_PER_USER", "MAX_ITEMS_PER_ROOM",
                 "MAX_INTERACTIONS_PER_ITEM", "MAX_NAME_LENGTH", "MAX_DESCRIPTION_LENGTH", "MAX_TEXT_LENGTH", "MAX_MAILS",
                 "MIN_FREE_MEMORY"):
        value = getattr(config, name)
        if type(value) is not int or value <= 0:
            raise ValueError(name + " must be a positive integer")


def main():
    import sys
    from modules import led

    server = None
    ap = None
    try:
        import config

        validate(config)
        from modules import wifi
        from modules.telnet import TelnetServer
        from controllers.telnet_controller import TelnetController
        from controllers.persistence_controller import PersistenceController
        from modules.commands import REGISTRY
        import gc

        print("PICO MUD boot:", sys.implementation)
        ap = wifi.start_ap(config.AP_SSID, config.AP_PASSWORD)
        led.blink(1)
        world = PersistenceController(config, REGISTRY)
        world.load()
        controller = TelnetController(world)
        server = TelnetServer(
            controller,
            port=config.TELNET_PORT,
            max_clients=config.MAX_CLIENTS,
            idle_timeout=config.IDLE_TIMEOUT,
            max_line_length=config.MAX_LINE_LENGTH,
        )
        server.start()
        led.blink(2)
        led.on()
        gc.collect()
        print("Free heap after startup:", gc.mem_free(), "bytes")
        server.run()
    except KeyboardInterrupt:
        raise
    except Exception as error:
        sys.print_exception(error)
        if server is not None:
            server.stop()
        led.fatal_loop()
    finally:
        if server is not None:
            server.stop()
        if ap is not None:
            ap.active(False)
        led.off()


if __name__ == "__main__":
    main()
