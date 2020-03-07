import json


from django.conf import (
    settings,
)
from django.core.management.base import (
    BaseCommand,
)
from django.utils import (
    timezone,
)


from ...models import (
    EmailTracker,
    MonthlyStat,
)


class Command(BaseCommand):
    help = 'Updates monthly stats with data from email trackers and deletes outdated trackers'

    def handle(self, *args, **options):
        current_datetime = timezone.now()
        monthly_stat, created = MonthlyStat.objects.get_or_create(
            year_int=current_datetime.year,
            month_int=current_datetime.month,
        )
        try:
            tracking_months = settings.EMAILER_TRACKING_MONTHS
        except AttributeError:
            tracking_months = 3
        for tracker in EmailTracker.objects.all():
            ''' Find and delete outdated trackers '''
            deletion_datetime_months = tracker.send_complete.year * 12 + tracker.send_complete.month + tracking_months
            current_datetime_months = current_datetime.year * 12 + current_datetime.month + 1
            if current_datetime_months > deletion_datetime_months:
                tracker.delete()
            else:
                ''' Find and attach any appropriate unattached trackers as current or older '''
                if tracker not in monthly_stat.current_trackers.all() \
                        and tracker not in monthly_stat.older_trackers.all() \
                        and tracker.json_data:
                    tracker_dict = json.loads(tracker.json_data)
                    for key, value in tracker_dict.items():
                        year = value[0]
                        month = value[1]
                        if year == current_datetime.year and month == current_datetime.month:
                            if current_datetime.year == tracker.send_complete.year \
                                    and current_datetime.month == tracker.send_complete.month:
                                monthly_stat.current_trackers.add(tracker)
                            else:
                                monthly_stat.older_trackers.add(tracker)
                            break
        ''' Create sorted list of subscription names '''
        subscription_names = []
        month_trackers = monthly_stat.current_trackers.all()
        for tracker in month_trackers:
            if tracker.subscription_name not in subscription_names:
                subscription_names.append(tracker.subscription_name)
        subscription_names.sort()
        ''' Append 'Older emails' to list of subscriptions if appropriate '''
        if monthly_stat.older_trackers.exists():
            subscription_names += ['Older emails']
        ''' Reset stat data and tallies '''
        monthly_stat.stat_data = ''
        for name in subscription_names:
            sent_tally = 0
            open_tally = 0
            monthly_stat.stat_data = \
                '{} \
                <tr id="emailer_title_row"> \
                <td>&nbsp;</td> \
                <td>{}</td> \
                <td id="emailer_numerical">Sent</td> \
                <td id="emailer_numerical">Opens</td> \
                <td></td> \
                </tr>'.format(monthly_stat.stat_data, name)
            ''' Get appropriate group of trackers '''
            if name == 'Older emails':
                subscription_trackers = monthly_stat.older_trackers.all()
            else:
                subscription_trackers = month_trackers.filter(
                    subscription_name=name,
                )
            stat_dict = {}
            for tracker in subscription_trackers:
                ''' Calculate tracker's opened number for current month '''
                if tracker.json_data:
                    opens = 0
                    tracker_dict = json.loads(tracker.json_data)
                    for key, value in tracker_dict.items():
                        year = value[0]
                        month = value[1]
                        if year == current_datetime.year and month == current_datetime.month:
                            opens += 1
                        ''' Create a list of stat data and add to stat dictionary '''
                        stat_dict[tracker.pk] = [
                            opens,
                            tracker.number_sent,
                            tracker.subject,
                            tracker.send_complete_string(),
                        ]
            ''' Sort stat dictionary '''
            sorted_by_value = sorted(stat_dict.items(), key=lambda kv: kv[1], reverse=True)
            if sorted_by_value:
                ''' Format data as rows '''
                row_number = 1
                for email in sorted_by_value:
                    if row_number & 1:
                        row_id = 'emailer_row_odd'
                    else:
                        row_id = 'emailer_row_even'
                    row_number_str = '{}.'.format(str(row_number))
                    tracker_data = email[1]
                    opens = '{:,}'.format(tracker_data[0])
                    sent = '{:,}'.format(tracker_data[1])
                    if tracker_data[0] != 0 and tracker_data[1] != 0:
                        percentage = '{:.1%}'.format(tracker_data[0] / tracker_data[1])
                    else:
                        percentage = '0%'
                    subject = tracker_data[2]
                    distribution_date = tracker_data[3]
                    monthly_stat.stat_data = \
                        '{} \
                        <tr id="{}"> \
                        <td id="emailer_numerical">{}</td> \
                        <td>{}<br>{}</td> \
                        <td id="emailer_numerical">{}</td> \
                        <td id="emailer_numerical">{}</td> \
                        <td id="emailer_numerical">{}</td> \
                        </tr>'.format(
                            monthly_stat.stat_data,
                            row_id,
                            row_number_str,
                            subject,
                            distribution_date,
                            sent,
                            opens,
                            percentage,
                        )
                    row_number += 1
                    sent_tally += tracker_data[1]
                    open_tally += tracker_data[0]
            total_opens = '{:,}'.format(open_tally)
            total_sent = '{:,}'.format(sent_tally)
            if open_tally != 0 and sent_tally != 0:
                total_percentage = '{:.1%}'.format(open_tally / sent_tally)
            else:
                total_percentage = '0%'
            monthly_stat.stat_data = \
                '{} \
                <tr id="emailer_title_row"> \
                <td><br><br></td> \
                <td id="emailer_numerical">Totals:<br><br></td> \
                <td id="emailer_numerical">{}<br><br></td> \
                <td id="emailer_numerical">{}<br><br></td> \
                <td id="emailer_numerical">{}<br><br></td> \
                </tr>'.format(
                    monthly_stat.stat_data,
                    total_sent,
                    total_opens,
                    total_percentage,
                )
        monthly_stat.save()
