require 'graphviz'

# Create a new graph
g = GraphViz.new( :G, :type => :digraph )
g[:size] = "8.27x11.7" #A4
#g[:size] = "11.7x16.5" #A3
g.node[:shape] = :plaintext


# From https://www.safaribooksonline.com/library/view/ruby-cookbook/0596523696/ch01s15.html
def wrap(s, width=35)
  s.gsub(/(.{1,#{width}})(\s+|\Z)/, "\\1<br/>")
end

def make_page_label(url, title, comment, content)
  result = '<' + 
           '<TABLE BORDER="0"><TR><TD ALIGN="LEFT">' + url + '</TD></TR><TR><TD>' +
	   '<TABLE BORDER="1" CELLSPACING="4" CELLBORDER="0">' +
	   '<TR><TD><B>' + title + '</B><BR ALIGN="CENTER"/>' +
           (comment ? '<I>' + wrap(comment) + '</I>' : '') +
	   '</TD></TR><TR><TD>' + content +
	   '</TD></TR></TABLE>' + 
	   '</TD></TR></TABLE>' +
           '>'
  return(result)
end

def make_button(text, default=false)
  result = "<TABLE BORDER=\"#{default ? "1" : "0"}\" CELLSPACING=\"0\"><TR>" +
           "<TD BORDER=\"1\" BGCOLOR=\"GRAY80\">" +
           text + "</TD></TR></TABLE>"
  return result
end

def make_text_box(text)
  result = "<TABLE BORDER=\"0\" CELLSPACING=\"0\"><TR>" +
           "<TD BORDER=\"1\" BGCOLOR=\"GRAY90\">" +
           wrap(text) + "</TD></TR></TABLE>"
  return result
end

def make_mock_page(title, content)
  result = "<TABLE BGCOLOR=\"YELLOW\" BORDER=\"1\" CELLSPACING=\"1\" CELLBORDER=\"0\">" +
	   "<TR><TD><B>" + title + "</B><BR ALIGN=\"LEFT\"/></TD></TR>" +
	   "<TR><TD>" + content + "</TD></TR>" +
	   "</TABLE>"
  return result
end

def make_edge_label(label)
  return("<<I>" + wrap(label, 10) + "</I>>")
end

def make_edge_box_label(label)
  return("<<TABLE BORDER=\"0\"><TR><TD BORDER=\"1\">" + wrap(label, 10) + "</TD></TR></TABLE>>")
end

welcome = g.add_nodes("welcome")
welcome[:label] = make_page_label(
  '/slat',
  'Welcome Page', 
  'In a cloud deployment, you would need to log in before getting here.',
  make_mock_page("Welcome to WebSLAT", 
                 "<TABLE BORDER=\"0\">" +
                 "<TR><TD COLSPAN=\"2\">Choose an existing project:</TD></TR>" +
                 "<TR><TD></TD><TD ALIGN=\"LEFT\"><U>Redbook example<BR ALIGN=\"LEFT\"/></U></TD></TR>" +
                 "<TR><TD></TD><TD ALIGN=\"LEFT\"><U>Project #1</U><BR ALIGN=\"LEFT\"/></TD></TR>" +
                 "<TR><TD></TD><TD ALIGN=\"LEFT\"><U>Project #2</U><BR ALIGN=\"LEFT\"/></TD></TR>" +
	         "<TR><TD COLSPAN=\"2\" ALIGN=\"CENTER\">Or</TD><TD></TD></TR>" +
                 "<TR><TD COLSPAN=\"2\">" + make_button("Create a new project", false) +
                 "</TD></TR></TABLE>"))

project_editor = g.add_nodes("project_editor")
project_editor[:label] = make_page_label(
  '/slat/project/id#',
  'Project Editor', 
  'This is the main page for the Redbook Example Project.',
  make_mock_page("Redbook Example", 
                 "<TABLE BORDER=\"0\" CELLSPACING=\"0\" CELLBORDER=\"0\">" +
                 "<TR><TD><B>Title</B></TD><TD>" + make_text_box("Redbook Project") + "</TD></TR>"  +
                 "<TR><TD><B>Description</B></TD><TD ALIGN=\"LEFT\">" + 
                 make_text_box("This project is based on the Redbook reference project") + 
                 "</TD></TR>"  +
                 "<TR><TD></TD><TD>" + make_button("Submit Changes") + "</TD></TR>" +
                 "<TR><TD HEIGHT=\"10\" COLSPAN=\"2\"></TD></TR>" +
                 "<TR><TD></TD><TD>" + make_button("Seismic Hazard") + "</TD></TR>" +
                 "<TR><TD></TD><TD>" + make_button("Engineering Demands") + "</TD></TR>" +
                 "<TR><TD></TD><TD>" + make_button("Component Library") + "</TD></TR>" +
                 "<TR><TD></TD><TD>" + make_button("Component Groups") + "</TD></TR>" +
                 "<TR><TD></TD><TD>" + make_button("Calculations") + "</TD></TR>" +
                 "</TABLE>"))

new_project = g.add_nodes("new_project")
new_project[:label] = make_page_label(
  '/slat/project',
  'New Project', 
  NIL,
  make_mock_page("Create a Project", 
                 "<TABLE BORDER=\"0\" CELLSPACING=\"0\" CELLBORDER=\"0\">" +
                 "<TR><TD><B>Title</B></TD><TD>" + make_text_box("<I>Enter the project's title</I>") + "</TD></TR>"  +
                 "<TR><TD><B>Description</B></TD><TD ALIGN=\"LEFT\">" + 
                 make_text_box("<I>Describe the project</I>") + 
                 "</TD></TR>"  +
                 "<TR><TD></TD><TD>" + make_button("Create") + "</TD></TR>" +
                 "<TR><TD></TD><TD>" + make_button("Cancel") + "</TD></TR>" +
                 "</TABLE>"))

save = g.add_nodes("save")
save[:label] = "<<I>" + wrap("Save the Project To the Database", 20) + "</I>>"
save[:shape] = :folder
save[:fillcolor] = :cornflowerblue
save[:style] = :filled

def make_page_ref(graph, name, title)
  node = graph.add_nodes(name)
  node[:label] = "<" + wrap(title, 10) + ">"
  node[:shape] = :box
  node[:fillcolor] = "cyan:darkslategray3"
  node[:style] = :filled
  return(node)
end

hazard_editor = make_page_ref(g, "hazard_editor", "Hazard Editor")
edp_editor = make_page_ref(g, "edp_editor", "EDP  Editor")
component_library = make_page_ref(g, "Component_library", "Component Library")
component_groups = make_page_ref(g, "Component_groups", "Component Groups")
calculations = make_page_ref(g, "calculations_", "Calculations")

g.add_edges( welcome, project_editor )[:label] = make_edge_label("Existing Project")
g.add_edges( welcome, new_project )[:label] = make_edge_label("Create a New Project")
g.add_edges( new_project, welcome )[:label] = make_edge_label("Cancel")
g.add_edges( new_project, save )[:label] = make_edge_label("Create")
g.add_edges( save, project_editor )
g.add_edges( project_editor, save )[:label] = make_edge_label("Submit Changes")
g.add_edges( project_editor, hazard_editor )[:label] = make_edge_box_label("Seismic Hazard")
g.add_edges( hazard_editor, project_editor )[:label] = make_edge_label("done")
g.add_edges( project_editor, edp_editor )[:label] = make_edge_box_label("Demand Parameters")
g.add_edges( edp_editor, project_editor )[:label] = make_edge_label("done")
g.add_edges( project_editor, component_library )[:label] = make_edge_box_label("Components")
g.add_edges( component_library, project_editor )[:label] = make_edge_label("done")
g.add_edges( project_editor, component_groups )[:label] = make_edge_box_label("Component Groups")
g.add_edges( component_groups, project_editor )[:label] = make_edge_label("done")
g.add_edges( project_editor, calculations )[:label] = make_edge_box_label("Calculations")
g.add_edges( calculations, project_editor )[:label] = make_edge_label("done")

# Generate output image
puts g.output( :none => String )
g.output( :png => "pages-test.png")
g.output( :pdf => "pages-test.pdf")

puts(wrap("EDP Editor", 10))
