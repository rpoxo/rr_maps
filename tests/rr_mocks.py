
class Mock_bf2(object):
    
    def __init__(self):
        self.Status = None
        
class Mock_host(object):
    
    class _MockGame(object):
    
        class _MockState(object):
            
            def __init__(self):
                self._input_log = []
                self._echo = []
        
        def __init__(self):
            self._state = self._MockState()
            self.__handlers = {
                'echo' : self.__handler_echo,
                }
            
        def send_to_handlers(self, input):
            self._state._input_log.append(input)
            self.command = input.split(' ')[0]
            self.__handlers[self.command](input)
        
        def __handler_echo(self, input):
            self._state._input_log.append(input)
            message = input.replace('echo ', '')
            message = message.replace('"', '').replace("'", '')
            self._state._echo.append(message)

    def __init__(self):
        self._game = self._MockGame()
    
    def timer_getWallTime(self):
        return 0
        
    def sgl_getModDirectory(self):
        return '.'
    
    def rcon_invoke(self, command):
        self._game.send_to_handlers(command)

class Mock_realitylogger(object):

    def __init__(self):
        self.RealityLogger = MockLogger()
    
    def createLogger(self, name, path, fileName, continous):
        self.RealityLogger.createLogger(name, path, fileName, continous)

class MockLogger(object):
    
    # holds loggers
    _loggers = { }
    
    def __init__(self):
        pass
        
    def __getitem__( self, key ):
        return self._loggers[key]

    def __len__( self ):
        return len( self._loggers )
    
    def createLogger(self, name, path, fileName, continous):
        if name not in self._loggers:
            self._loggers[name] = self.__Logger( path, fileName, continous )
    
    class __Logger(object):

        def __init__(self, path, fileName, continous):
            self.__path = path
            self.__fileName = fileName
            self.__continous = continous
            
            self.messages = []
        
        def logLine(self, msg):
            self.messages.append(msg)

class MockInterface(object):

    def __init__(self):
        self.__logger = MockLogger()
        self.__host = Mock_host()
    
    def get_wall_time(self):
        return 0
    
    def create_logger(self, name, path, fileName, continous):
        return self.__logger.createLogger(name, path, fileName, continous)
    
    def send_logger_logLine(self, name, msg):
        return self.__logger.__loggers[name].logLine(msg)
    
    def debug_echo(self, msg):
        self.__host.rcon_invoke("echo \"" + str(msg) + "\"")
        
    def get_mod_directory(self):
        return '.'