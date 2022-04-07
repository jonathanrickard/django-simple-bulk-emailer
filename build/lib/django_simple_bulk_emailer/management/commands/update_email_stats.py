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
                    for key, value in tracker.json_data.items():
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
                f'{monthly_stat.stat_data}' \
                f'<tr id="emailer_title_row">' \
                f'<td>&nbsp;</td>' \
                f'<td>{name}</td>' \
                f'<td id="emailer_numerical">Sent</td>' \
                f'<td id="emailer_numerical">Opens</td>' \
                f'<td></td>' \
                f'</tr>'
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
                    for key, value in tracker.json_data.items():
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
                    row_number_str = f'{str(row_number)}.'
                    tracker_data = email[1]
                    opens = f'{tracker_data[0]:,}'
                    sent = f'{tracker_data[1]:,}'
                    if tracker_data[0] != 0 and tracker_data[1] != 0:
                        percentage = f'{tracker_data[0] / tracker_data[1]:.1%}'
                    else:
                        percentage = '0%'
                    subject = tracker_data[2]
                    distribution_date = tracker_data[3]
                    monthly_stat.stat_data = \
                        f'{monthly_stat.stat_data}' \
                        f'<tr id="{row_id}">' \
                        f'<td id="emailer_numerical">{row_number_str}</td>' \
                        f'<td>{subject}<br>{distribution_date}</td>' \
                        f'<td id="emailer_numerical">{sent}</td>' \
                        f'<td id="emailer_numerical">{opens}</td>' \
                        f'<td id="emailer_numerical">{percentage}</td>' \
                        f'</tr>'
                    row_number += 1
                    sent_tally += tracker_data[1]
                    open_tally += tracker_data[0]
            total_opens = f'{open_tally:,}'
            total_sent = f'{sent_tally:,}'
            if open_tally != 0 and sent_tally != 0:
                total_percentage = f'{open_tally / sent_tally:.1%}'
            else:
                total_percentage = '0%'
            monthly_stat.stat_data = \
                f'{monthly_stat.stat_data}' \
                f'<tr id="emailer_title_row">' \
                f'<td><br><br></td>' \
                f'<td id="emailer_numerical">Totals:<br><br></td>' \
                f'<td id="emailer_numerical">{total_sent}<br><br></td>' \
                f'<td id="emailer_numerical">{total_opens}<br><br></td>' \
                f'<td id="emailer_numerical">{total_percentage}<br><br></td>' \
                f'</tr>'
        monthly_stat.save()
