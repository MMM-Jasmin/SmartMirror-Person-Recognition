/**
 * @file smartmirror-person-recognition.js
 *
 * @author madams
 * @license MIT
 *
 * 
 */

Module.register('SmartMirror-Person-Recognition',{

	defaults: {
		// camera image size. This module has no image output!
		image_height: 1080,
		image_width: 1920
	},

	start: function() {
		this.time_of_last_greeting_personal = [];
		this.time_of_last_greeting = 0;
		this.last_rec_user = [];
		this.current_user = null;
		this.sendSocketNotification('CONFIG', this.config);
		Log.info('Starting module: ' + this.name);
	},

	notificationReceived: function(notification, payload, sender) {
		if (notification === "/gesture_det/gestures") {
			this.sendSocketNotification('DETECTED_GESTURES', payload);
		}else if (notification === '/face_det/json_out') {
			this.sendSocketNotification('DETECTED_FACES', payload);
		}else if (notification === '/object_det/objects') {
			this.sendSocketNotification('DETECTED_OBJECTS', payload);
		}
	},

	socketNotificationReceived: function(notification, payload) {
		var self = this;
		if(notification === 'RECOGNIZED_PERSONS') {
			this.sendNotification('RECOGNIZED_PERSONS', payload);
			//console.log("[" + this.name + "] " + "gesture detected: " + payload);
        };
	}
});
