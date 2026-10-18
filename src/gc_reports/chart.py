import xy

from gc_reports.algebra import RealNumber


def stacked_bar_chart(
    title: str,
    x_axis: str,
    x_labels: list[str],
    y_axis: str,
    y_data: list[tuple[str, list[RealNumber]]],
) -> None:
    """
    Generate a stacked bar chart using the provided data.
    :param title: Title of the chart
    :param x_axis: Label for the x-axis
    :param x_labels: Labels for the x-axis (e.g., months)
    :param y_axis: Label for the y-axis
    :param y_data: List of tuples where each tuple contains a category name and its corresponding values for each x_label
    """

    bars = [
        xy.bar(x_labels, [float(value) for value in values], name=category_name)
        for category_name, values in y_data
    ]
    chart = xy.bar_chart(
        *bars,
        xy.x_axis(label=x_axis),
        xy.y_axis(label=y_axis),
        xy.legend(loc="best", ncols=2),
        title=title,
    )

    chart.to_html(f"{title.replace(' ', '_').lower()}.html")
