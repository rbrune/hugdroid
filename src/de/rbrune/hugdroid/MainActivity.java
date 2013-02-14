package de.rbrune.hugdroid;

import android.os.Bundle;
import android.os.PowerManager;
import android.os.SystemClock;
import android.provider.Settings;
import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.view.Menu;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.view.WindowManager.LayoutParams;

public class MainActivity extends Activity {
	PowerManager.WakeLock sScreenWakeLock;
	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);

		requestWindowFeature(android.view.Window.FEATURE_NO_TITLE);
		getWindow().addFlags(WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED);
		setContentView(R.layout.activity_main);
	}

	protected void onStart() {
		super.onStart();
		
		if (sScreenWakeLock == null) {
			PowerManager pm = (PowerManager) getSystemService(Context.POWER_SERVICE);
			sScreenWakeLock = pm.newWakeLock(PowerManager.FULL_WAKE_LOCK | PowerManager.ACQUIRE_CAUSES_WAKEUP | PowerManager.ON_AFTER_RELEASE, "MainActivity Wakelock");
			sScreenWakeLock.acquire();
		}
		
		
		Intent i = getIntent();
		evalIntent(i);
	}

	protected void onNewIntent(Intent i) {
		evalIntent(i);
	}
	
	protected void onStop() {
		if (sScreenWakeLock != null) {
			sScreenWakeLock.release();
			sScreenWakeLock = null;
		}
		super.onStop();
		
	}
	
	protected void evalIntent(Intent i) {

		if ((i != null) && (i.hasExtra("color"))) {
			String newcolor = i.getStringExtra("color");
			
			View layout = findViewById(R.id.mainlayout);
			layout.setBackgroundColor(Color.parseColor(newcolor));
		}

		if ((i != null) && (i.hasExtra("brightness"))) {
			Float brightness = Float.parseFloat(i.getStringExtra("brightness"));
			Window window = getWindow();
			WindowManager.LayoutParams lp = window.getAttributes();
			lp.screenBrightness = brightness;
			window.setAttributes(lp);
			Settings.System.putInt(getContentResolver(), Settings.System.SCREEN_BRIGHTNESS, (int)(brightness*255));
		}
		
		if ((i != null) && (i.hasExtra("sleep"))) {
			//PowerManager pm = (PowerManager) getSystemService(Context.POWER_SERVICE);
			//pm.goToSleep(SystemClock.uptimeMillis());
			if (sScreenWakeLock != null) {
				sScreenWakeLock.release();
				sScreenWakeLock = null;
			}
			WindowManager.LayoutParams params = getWindow().getAttributes(); 
			params.flags |= LayoutParams.FLAG_KEEP_SCREEN_ON; 
			params.screenBrightness = 0; 
			getWindow().setAttributes(params);
		}
	}
	
}
