library(shiny)
library(shinythemes)
library(shinyREDCap)
library (reactable)
library(httr)
library(stringi)
library(jsonlite)
library(DT)
library(reticulate)
library(shinyWidgets)
library(rjson)


# Allow for multiple options to be selected per filter

# Setting up UI
ui <- fluidPage(theme = shinytheme('cerulean'),
  navbarPage(
    
    "REDCap App (V1.0)",
    
    # Data fetching and pipeline running tab
    tabPanel("Data Fetch & Pipeline Runner",
      
      # Filter sidebar
      sidebarPanel(
        
        tags$h3('Filters:'),
        
        helpText('View and export demographic information as filtered.'),
        
        textInput('project',
                  label = 'Projects:', ''),
        
        actionButton('getFields', 'Get Options'),
        
        uiOutput('formsDrop'),
        
        uiOutput('fieldsDrop'),
        
        uiOutput('armsDrop'),
        
        uiOutput('eventsDrop'),
        
        uiOutput('recordsText'),
        
        # textInput('fields',
        #           label = 'Fields:', ''),
        # 
        # textInput('forms',
        #           label = 'Forms:', ''),
        # 
        # textInput('arm',
        #           label = 'Arm:', ''),
        # 
        # textInput('events',
        #           label = 'Events:', ''),
        # 
        # textInput('pipe',
        #           label = 'Pipe:', ''),
        # 
        # textInput('records',
        #           label = 'Records:', ''),
        
        # Execute fetch
        h3(''),
        
        actionButton('updateUrl', 'Analyze Output'),
        
        # Outputted URL
        h3('Current URL:'),
        
        verbatimTextOutput('url')
        
      ),
      
      # Displays resulting data table from filters
      mainPanel(
  
        h1('Data Viewer:'),
        
        tableOutput('table'),
        
        # Download data table as csv
        downloadButton('downloadData', 'Download'),
        
        downloadButton("fakeDownload", label = "Download and Open D-Tale")
        
      )
    ),
    
    # Project adding tab
    tabPanel(
      
      title = "Add, Remove, Update a Project",
      
      h1('Status:'),
      
      verbatimTextOutput('status'),
      
      hr(),
      
      fluidRow(
        column(3,
               # User requirements for adding a project to REDCap database
               #tags$h3('Project Details:'),
               
               helpText('Add a project on REDCap. Please provide the project name, url, and token.'),
               
               textInput('new_proj', 'Project Name:', ''),
               
               textInput('new_URL', 'Project URL:', ''),
               
               textInput('new_token', 'Project Token:', ''),
               
               # Execute adding a project
               actionButton('add_Proj', 'Add Project'),
               
               verbatimTextOutput('add_results')
               
        ),
        column(4, offset = 1,
               helpText('Remove a project on REDCap. Please provide the project name. '),
               
               textInput('rem_proj', 'Project Name:', ''),
               
               actionButton('remove', 'Remove Project'),
               
               verbatimTextOutput('rem_results')
        ),
        column(4,
               helpText('Update a project on REDCap. Please provide the updated project name, url, or token.'),
               
               textInput('upd_proj', 'New Project Name:', ''),
               
               textInput('upd_URL', 'New Project URL:', ''),
               
               textInput('upd_token', 'New Token URL', ''),
               
               actionButton('update', 'Update Project'),
               
               verbatimTextOutput('upd_results')
        )
      )
      # "Add a Project",
      # 
      # sidebarPanel(
      #   
      #   # User requirements for adding a project to REDCap database
      #   tags$h3('Project Details:'),
      #   
      #   helpText('Add a project on REDCap. Please provide the project name, url, and token.'),
      #   
      #   textInput('new_proj', 'Project Name:', ''),
      #   
      #   textInput('new_URL', 'Project URL:', ''),
      #   
      #   textInput('new_token', 'Project Token:', ''),
      #   
      #   # Execute adding a project
      #   actionButton('add_Proj', 'Add Project'),
      #   
      #   verbatimTextOutput('add_results')
      #   
      # ),
      # 
      # mainPanel(
      #   
      #   # Display success/error in adding project
      #   h1('Status:'),
      #   
      #   verbatimTextOutput('status')
      # )
    ),
    
    # Adding a pipe tab
    # TODO: Implement Pipe adding functionality
    tabPanel(
      
      "Add a Pipe",
      
      textAreaInput('pipecode', 'Code for Pipes:', width='1000px', height = '500px'),
      
      verbatimTextOutput('code'),
      
      downloadButton('downloadPipe', 'Download Pipe')
    )
  )
)



################### Setting up server ######################################
server <- function(input, output) {
  #####################################
  # Data Fetch
  
  
  # Basic url for data fetching
  baseurl <- 'http://127.0.0.1:8000/redcap/'
  
  # Reactive string of parameters for url fetch
  querystring <- reactiveVal()
  
  csv_file <- reactiveVal()
  
  # Parameter specific urls for getting dropdowns
  formsurl <- 'http://127.0.0.1:8000/forms/'
  fieldsurl <- 'http://127.0.0.1:8000/fields/'
  armsurl <- 'http://127.0.0.1:8000/arms/'
  eventsurl <- 'http://127.0.0.1:8000/events/'
  
  
  # Retrieving project name to begin fetching dropdowns
  projecturl <- reactive({
    if (input$project == '')
      return(NULL)
    else
      return(input$project)
    
  })
  
  
  # When user executes data fetch (pressing action button)
  observeEvent(input$getFields, {
    
    
    # Fetch the urls for each parameter and output them
    forms <- content(GET(paste0(formsurl, projecturl())))
    formsOptions <- c('\n')
    for(i in 1:length(forms)){
      formsOptions <- c(formsOptions, forms[i])
    }
    
    output$formsDrop <- renderUI({
      if (length(forms) == 0)
        return(NULL)
      selectInput('forms', 'Forms:', formsOptions)
    })
      
    fields <- content(GET(paste0(fieldsurl, projecturl())))
    fieldsOptions <- c('\n')
    for(i in 1:length(fields)){
      fieldsOptions <- c(fieldsOptions, fields[i])
    }
    
    output$fieldsDrop <- renderUI({
      if (length(fields) == 0)
        return(NULL)
      pickerInput('fields', 'Fields:', fieldsOptions, multiple = FALSE, options = pickerOptions(maxOptions = 10000, liveSearch = TRUE))
    })
    
    # for arms, only get nums as 'type'
    armsNums <- content(GET(paste0(armsurl, projecturl(), '/nums')))
    armsOptions <- c('\n')
    for(i in 1:length(armsNums)){
      armsOptions <- c(armsOptions, armsNums[i])
    }

    output$armsDrop <- renderUI({
      if (length(armsOptions) == 1)
        return(NULL)
      selectInput('arms', 'Arms:', armsOptions)
    })
    
    events <- content(GET(paste0(eventsurl, projecturl())))
    eventsOptions <- c('\n')
    for(i in 1:length(events)){
      eventsOptions <- c(eventsOptions, events[i])
    }
    
    output$eventsDrop <- renderUI({
      if (length(events) == 0)
        return(NULL)
      selectInput('events', 'Events:', eventsOptions)
    })
    
    output$recordsText <- renderUI({
      textInput('records', 'Records:')
    })
  
  })
  
  # Reactively updating filter variables with user input
  
  fieldsPar <- reactive({
    if (input$fields == '\n')
      return(NULL)
    else
      return(paste0('fields=', input$fields))
  })
  formsPar <- reactive({
    if (input$forms == '\n')
      return(NULL)
    else
      return(paste0('forms=', input$forms))
  })
  
  armsPar <- reactive({
    if (input$arms == '\n')
      return(NULL)
    else
      return(paste0('arms=', input$arms))
  })
  
  eventsPar <- reactive({
    if (input$events == '\n')
      return(NULL)
    else
      return(paste0('events=',input$events))
  })
  
  # pipesPar() <- reactive({
  #   if (input$pipe == '')
  #     return(NULL)
  #   else
  #     return(paste0('pipe=',input$pipe))
  # })
  
  recordsPar <- reactive({
    if (input$records == '')
      return(NULL)
    else
      return(paste0('records=', input$records))
  })
  
  # Actions when fetch button is pressed
  observeEvent( input$updateUrl, {
    
    # Creates string with up-to-date filter parameters
    new_query <-
    stri_paste(formsPar(), fieldsPar(), eventsPar(), armsPar(), recordsPar(), sep='&', ignore_null = TRUE)
    
    # Assigns string to reactive string
    querystring(new_query)
    
    
    # fetch finalized data query
    r <- content(GET(paste0(baseurl,projecturl(), '/?',querystring())))
    
    # process json to display as data table
    json_file <- lapply(r, function(x) {
      x[sapply(x, is.null)] <- NA
      unlist(x)
    })
    
    # create dataframe for output
    df <- data.frame(do.call('cbind', json_file))
    csv_file(df)
    
  
    #Output data table to UI
    output$table <- renderTable({
      df
    })

    
    # Download data from table as a .csv
    # file name follows format: 'data-{date of download}.csv'
    output$downloadData <- downloadHandler(
      filename = function(){

        paste("data-", Sys.Date(), ".csv", sep="")
      },
      content = function(file){
        write.csv(df, file)
        print(file)
      }
    )
    
    
    
  })
  
  #Output reactive URL to UI
  output$url <- renderText({
    paste0(baseurl,projecturl(), '/?', querystring())
  })
  
  
  
  #observeEvent(input$openDtale, {
    
  output$fakeDownload <- downloadHandler(
    fname <- stringr::str_replace_all(stringr::str_replace(Sys.time(), " ", "_"), ":", "_"),
    filename = function(){
      paste("data-", fname, ".csv", sep="")
    },
    content = function(file){
      if (!dir.exists('~/.greencap/dtale')){
        dir.create("~/.greencap/dtale")
      }
      write.csv(csv_file(), paste0('~/.greencap/dtale/data-',fname, '.csv'))
      
      system(paste0("python3 open_dtale.py ", paste0('~/.greencap/dtale/data-',fname, '.csv')))
    }
  )
    #)
    
    #filename <- paste0("data-", Sys.time(), ".csv")
    
    
    #csv_file(paste0('~/.greencap/dtale/', filename))
    #write.csv(df, paste0('~/.greencap/dtale/', filename))
    
    
  
  
  ###############################################
  # Add a Project
  
  # function to add a project to either the local system or lab database
  # Currently only handles local functionality
  
  create_project <- function(name, url, token, local=TRUE){
    
    tryCatch({
      
      # if local is true
      if(local){
        
        
        # access path with projects
        greencap_user_cfg <- path.expand('~/.greencap/projects')
        
        # retrieve all files in 'projects' folder
        local_files <- list.files(greencap_user_cfg)
        
        # add extension to project name for json creation
        name_ext <- paste0(name, ".json")
        
        # if file is already located locally, return FALSE and inform user
        if (name_ext %in% local_files){
          
          output$add_results <- renderText({
            paste0("Project already contained locally!")
          })
          return(FALSE)
        }
        
        # create 2-D vector of url and token
        redcap_cred_list <- list(url,token)
        names(redcap_cred_list) <- c("url", "token")
        
        # convert vector to json file and write to 'projects' folder
        json_proj <- toJSON(redcap_cred_list)
        write(json_proj, paste0('~/.greencap/projects/',name,".json"))
      }
    }, error = function(e){
      
      # error message if all else fails and return FALSE
      output$add_results <- renderText({
        paste0("Error in project creation.")
      })
      return(FALSE)
    })
    
    # if added successfully, return TRUE
    return(TRUE)
    
  }
  
  delete_project <- function(name, local=TRUE){
    
    tryCatch({
      
      if(local){
        
        # access path with projects
        greencap_user_cfg <- path.expand('~/.greencap/projects')
        
        # retrieve all files in 'projects' folder
        local_files <- list.files(greencap_user_cfg)
        
        # add extension to project name for json creation
        name_ext <- paste0(name, ".json")
        
        # if file is already located locally, return FALSE and inform user
        if (name_ext %in% local_files){
          
          file_to_remove <- paste0('~/.greencap/projects/',name_ext)
          file.remove(file_to_remove)
          
          return(TRUE)
        
        } else{
          
          output$rem_results <- renderText({
            paste0("Project not contained locally!")
            
          })
          return(FALSE)
        }
      }
    }, error = function(e){
      
      # error message if all else fails and return FALSE
      output$rem_results <- renderText({
        paste0("Error in project creation.")
      })
      return(FALSE)
      
    })
  }
  
  update_project <- function(name, url, token, local=TRUE){
    
    tryCatch({
      
      if(local){
        
        # access path with projects
        greencap_user_cfg <- path.expand('~/.greencap/projects')
        
        # retrieve all files in 'projects' folder
        local_files <- list.files(greencap_user_cfg)
        
        # add extension to project name for json creation
        name_ext <- paste0(name, ".json")
        
        # if file is already located locally, return FALSE and inform user
        if (name_ext %in% local_files){
          
          # create 2-D vector of url and token
          redcap_cred_list <- list(url,token)
          names(redcap_cred_list) <- c("url", "token")
          
          # convert vector to json file and write to 'projects' folder
          json_proj <- toJSON(redcap_cred_list)
          write(json_proj, paste0('~/.greencap/projects/',name,".json"))
          
        } else{
          
          output$upd_results <- renderText({
            paste0("Project not contained locally!")
            
          })
          return(FALSE)
        }
      }
    }, error = function(e){
      
      # error message if all else fails and return FALSE
      output$upd_results <- renderText({
        paste0("Error in project creation.")
      })
      return(FALSE)
      
    })
    
    return(TRUE)
  }
  
  
  # if the user selects "add project"
  observeEvent(input$add_Proj, {
    
    # if fields are empty, return FALSE and let the user know 
    # (shouldn't be reactive)
    if(input$new_proj == '' | input$new_URL == '' | input$new_token == ''){
      output$add_results <- renderText({
        paste('Please provide all required information.')
      })
      
    }
    
    else{
   
      # attempt to create project with inputted fields, returns boolean
      results <- create_project(input$new_proj, input$new_URL, input$new_token, local = TRUE)
      
      # if true, project was added successfully
      if(results){
        
        output$status <- renderText({
          paste0("Project Added Successfully: ", input$new_proj)
          
        })
        output$add_results <- renderText({
          paste('')
        })
      }
      
      # If false, project was not added successfully
      else{
        output$status <- renderText({
          paste0("Project could not be added: ", input$new_proj)
        })
      }
    }
      
  })
  
  
  observeEvent(input$remove, {
    
    if(input$rem_proj == ''){
      output$rem_results <- renderText({
        paste('Please provide all required information.')
      })
    }
    
    else{
      
      results <- delete_project(input$rem_proj, local = TRUE)
      
      if(results){
        
        output$status <- renderText({
          paste0('Project Removed Successfully: ', input$rem_proj)
          
        })
        output$rem_results <- renderText({
          paste('')
        })
      }
    }
    
  })
  
  observeEvent(input$update, {
    
    # if fields are empty, return FALSE and let the user know 
    # (shouldn't be reactive)
    if(input$upd_proj == '' | input$upd_URL == '' | input$upd_token == ''){
      output$upd_results <- renderText({
        paste('Please provide all required information.')
      })
      
    }
    
    else{
      
      # attempt to create project with inputted fields, returns boolean
      results <- update_project(input$upd_proj, input$upd_URL, input$upd_token, local = TRUE)
      
      # if true, project was added successfully
      if(results){
        
        output$status <- renderText({
          paste0("Project Updated Successfully: ", input$upd_proj)
          
        })
        output$upd_results <- renderText({
          paste('')
        })
      }
      
      # If false, project was not added successfully
      else{
        output$status <- renderText({
          paste0("Project could not be updated: ", input$upd_proj)
        })
      }
    }
    
  })
  
}

# Run App
shinyApp(ui=ui, server=server)
