# System structure

[Architecture Diagram](connext-monitor.png)

There will be an monitoring module (used to monitor on chain contract to keep track on protocol states), as well
as an alerting module (used to alert warnings on various channels).

## Monitoring
Monitoring is done with a main monitoring thread. For each chain, an observer will be subscribing main Connext contract events. Once an event is receieved, it obtains the block timestamp and then send to a work queue for Transfer Checker to process.

## Transfer Checker
The transfer checkers recieve on chain events monitored by observers in a work queue. It decodes the log data, and process if its one of XCalled, Executed or Reconcile events.

For XCalled event, it insert a record to the database, then schedule two future alert (one for reconcile, one for execute) into the alert scheduler in case it is overtime.

For Executed/Reconcile event, it update the record to database, then cancel the execute/reconcile alert for this transfer.

## Alerting
Alerting is done via a alert scheduler, manager, and providers.
The transfer checker will schedule alerts through the scheduler. If an alert is not cancelled before its run time, then it will be send to the alert manager through a channel.

The alert manager manage a work queue for each providers. Upon request, it will put the alert task into the work queues.

The alert providers send out alert for different channel (Discord etc) when it recieve an alert task via the work queue.

## Future improvement
When the system is down and up again, currently it will not track the events happened between the downtime. A better way will be making the contract observers store processed block number periodically, so they can recover for failure and getting the past events.

Due to the time, a stat reporter is not in place. A periodic checker can be used to query the database for all the latency in the period.

More unit test and error reporting facility is required for the system.

## Configuration

TOML is used here for the configuration for its simplicity.

## Language Choice

Python is used here for rapid development and ease of blockchain library access.
