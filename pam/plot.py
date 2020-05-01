def plot_activities(person):
'''
Plot a high level activity plan for a single person
'''
    
    #Load a df with a persons activty plan
    activities, start_times, end_times, durations = [], [], [], []

    for component in person.plan.day:
        activities.append(component.act.title())
        start_times.append(component.start_time.hour + component.start_time.minute/60)
        end_times.append(component.end_time.hour + component.end_time.minute/60)
        durations.append(component.duration.total_seconds()/3600)

    df = pd.DataFrame(zip(activities,start_times,durations), columns=['act','start_time','dur'])

    #Define a colour map for a unique list of activities

    colors = plt.cm.tab10.colors
    activities_unique = df['act'].unique()


    d_color = dict(zip(activities_unique,colors))

    df['color'] = df['act'].map(d_color)


    #Plotting
    fig,ax = plt.subplots(figsize=(16,4))
    
    label_x, label_y = [],[]

    for i in range(len(df)):
        y = 1
        data = df.iloc[i]
        ax.barh(y, 
                width='dur', 
                data=data,
                left='start_time',
                label='act',
                color='color'
               )
        
        #Populate Labelling Params
        label_x.append(data['start_time']+data['dur']/2)
        label_y.append(y)
    
    #Labels
    rects = ax.patches
    
    for x, y, rect, activity in zip(label_x, label_y, rects, activities):
        if rect.get_width()>=3:
            ax.text(x, y, activity, ha='center',
                    fontdict={'color':'white', 'size':14, 'weight':'bold'})
        
    plt.xticks(range(25))
    plt.xlim(right=24)
    ax.get_yaxis().set_visible(False)