from .plot_average_data import PlotAverageData


class BokehPlotManager:
    """
    Create a new bokeh app for each instance that is opened.
    """

    def __init__(self, rti_config):
        """
        Initialize the object.
        :param rti_config: RTI Config.
        """
        self.rti_config = rti_config
        self.bokeh_app_list = []

    def setup_bokeh_server(self, doc):
        """
        Create a Bokeh App for the bokeh server.
        Each webpage open needs its own instance of PlotAverageData.
        :param doc: Doc to load for the webpage
        :return:
        """

        # Create a Plot Average Data object
        pad = PlotAverageData(self.rti_config)

        # Add the PlotAverageData to the list
        self.bokeh_app_list.append(pad)

        # Initialize the bokeh server with the plots
        pad.setup_bokeh_server(doc)

    def update_dashboard(self, avg_df):
        """
        Update all the created dashboards in the list.
        :param avg_df: Dataframe containing the latest data.
        :return:
        """
        for app in self.bokeh_app_list:
            app.update_dashboard(avg_df)
