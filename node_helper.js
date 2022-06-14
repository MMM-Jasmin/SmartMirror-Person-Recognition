'use strict';
const NodeHelper = require('node_helper');

const {PythonShell} = require('python-shell');
const { exec } = require('child_process');
var pythonStarted = false

module.exports = NodeHelper.create({

	python_start: function () {
		const self = this;		

		
		self.pyshell = new PythonShell('modules/' + this.name + '/python/person_recognition.py', {pythonPath: 'python3',  args: [JSON.stringify(this.config)]});
    		
		self.pyshell.on('message', function (message_string) {
			try{
				var message = JSON.parse(message_string)
           		//console.log("[MSG " + self.name + "] " + message);
				if (message.hasOwnProperty('status')){
					console.log("[" + self.name + "] " + JSON.stringify(message.status));
  				} else if (message.hasOwnProperty('RECOGNIZED_PERSONS')){
					//console.log("[" + self.name + "] " + JSON.stringify(message));
					self.sendSocketNotification('RECOGNIZED_PERSONS', message);
				}
			}
			catch(err) {
				console.log(err)
			}
   		});
		exec(`renice -n 20 -p ${self.pyshell.childProcess.pid}`,(error,stdout,stderr) => {
				if (error) {
					console.error(`exec error: ${error}`);
  				}
			});
  	},

  	// Subclass socketNotificationReceived received.
  	socketNotificationReceived: function(notification, payload) {
		const self = this;
		//console.log("[" + self.name + "] " + notification + " " + JSON.stringify(payload));	
		if (notification === 'DETECTED_GESTURES'){
			self.pyshell.send(payload);
		}else if (notification === 'DETECTED_OBJECTS'){
			self.pyshell.send(payload);
		}else if (notification === 'DETECTED_FACES'){
			self.pyshell.send(payload);
		}else if(notification === 'CONFIG') {
      		this.config = payload
      		if(!pythonStarted) {
        		pythonStarted = true;
        		this.python_start();
      		};
    	};
  	},

	stop: function() {
		const self = this;
		self.pyshell.childProcess.kill('SIGKILL');
		self.pyshell.end(function (err) {
           	if (err){
        		//throw err;
    		};
    		console.log('finished');
		});
	}
});
