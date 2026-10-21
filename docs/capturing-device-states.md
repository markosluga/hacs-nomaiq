# Capturing device states

Use this guide to add support for a Noma IQ device the integration doesn't handle yet. You change one setting at a time in the app, record the state the cloud reports for each change, and send the results to the project.

## Steps

1. **Set up the integration** in Home Assistant so your devices load.
2. **Pick a starting point.** Set the device in the app to a known state.
3. **Make one change in the app.** For example, set the fan to slow.
4. **Describe the change and capture the state.** In Home Assistant, go to **Developer Tools > Actions**, choose **Noma IQ: Capture device state**, select your device, type a short description of the change, and run it. The description should match what you did in the app.
5. **Repeat** steps 3 and 4 for each setting or combination you want to cover. Take at least one capture for every value the app offers.
6. **Download diagnostics.** Go to **Settings > Devices & services > Noma IQ**, open the menu, and choose **Download diagnostics**. Save the file.
7. **Open an issue** at the project's issue tracker and choose **Add device support**. Attach the diagnostics file and fill in the table of changes.

## What the diagnostics file contains

- Each device's name, `oem_model`, model number, and property values.
- Every capture you made, with its timestamp, description, and the property values at that moment.

It doesn't contain your username, password, or device serial numbers. Device names are included, so check them before you share the file.

## Notes

- Captures are kept in memory. Restarting Home Assistant clears them, so download diagnostics before you restart.
- Each capture asks the cloud for fresh values before recording. If the value you expect doesn't show up, wait a few seconds after the app change and capture again.
- The cloud can lag behind the app. If a capture disagrees with the app, note it in the issue.
