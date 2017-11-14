require 'graphviz'

class PageLayout < GraphViz
  def initialize()
    super(:G, :type => :digraph)
    self[:size] = "8.27x11.7"
    node[:shape] = :plaintext
  end

  def add_bubble(text, dotted=NIL, color=:white)
    node = add_nodes(text)
    node[:label] = text
    node[:shape] = :ellipse
    node[:style] = "filled"
    if dotted then
      node[:style] = node[:style] + ", dashed"
    end
    node[:color] = color
    node[:penwidth] = 3
    return node
  end

  def add_page(name, url, title, comment, page)
    node = add_nodes(name)
    node[:label] = "<" +
                   "<TABLE BORDER=\"0\">" +
                   "<TR><TD ALIGN=\"LEFT\">#{url}</TD></TR>" +
                   "<TR><TD><TABLE BORDER=\"1\" CELLSPACING=\"4\" CELLBORDER=\"0\">" +
                   "<TR><TD ALIGN=\"CENTER\"><B>#{title}</B><BR/>" +
                   (comment ? "<I>#{comment.wrap()}</I>" : "") +
                   "</TD></TR>" +
                   "<TR><TD>#{page}</TD></TR>" +
                   "</TABLE>" +

                   "</TD></TR></TABLE>" +
                   ">"
    return node
  end

  def add_action(name, description, width=NIL)
    node = add_nodes(name)
    node[:shape] = :folder
    node[:fillcolor] = :cornflowerblue
    node[:style] = :filled
    if width
      node[:label] = "<<I>#{description.wrap(width)}</I>>"
    else
      node[:label] = "<<I>#{description.wrap()}</I>>"
    end
    return node
  end

  def add_page_ref(name, title)
    node = add_nodes(name)
    node[:label] = "<" + title.wrap(10) + ">"
    node[:shape] = :box
    node[:fillcolor] = "cyan:darkslategray3"
    node[:style] = :filled
    return(node)
  end
  
  def connect(a, b, label=NIL)
    edge = add_edges(a, b)
    edge[:label] = "<<I>#{label.wrap(10)}</I>>" if label
    return edge
  end

end

class String
  def wrap(width=35)
    self.gsub(/(.{1,#{width}})(\s+|\Z)/, "\\1<BR ALIGN=\"LEFT\"/>")    
  end
end

class Label
  def initialize(text, width=NIL)
    @text = text
    @width = width
  end

  def to_s
    if width then
      @text.wrap()
    else
      @text.wrap(width)
    end
  end
end

class Mock_Page
  def initialize(title,&block)
    @title = title
    @contents = ""
    block.call(self) if block
  end

  def add_line(line)
    @contents = "#{@contents}<TR><TD COLSPAN=\"2\">#{line}</TD></TR>"
  end

  def add_space()
    @contents = "#{@contents}<TR><TD COLSPAN=\"2\"></TD></TR>"
  end
  
  def add_value(title, value)
    @contents = "#{@contents}<TR><TD>#{title}</TD><TD BORDER=\"1\">#{value}</TD></TR>"
  end    

  def add_text_box(title, value)
    @contents = "#{@contents}<TR><TD>#{title}</TD><TD BORDER=\"1\" BGCOLOR=\"GRAY90\">#{value}</TD></TR>"
  end    

  def add_list(values)
    @contents = "#{@contents}<TR><TD></TD><TD>"
    values.each {|v|
      @contents = "#{@contents}#{v}<BR ALIGN=\"LEFT\"/>"
    }
    @contents = "#{@contents}</TD></TR>"
  end

  def add_choices(label, values)
    @contents = "#{@contents}<TR><TD>#{label}</TD><TD>" +
                "<TABLE BORDER=\"0\" CELLBORDER=\"1\" BGCOLOR=\"GRAY90\">"
    values.each {|v|
      @contents = "#{@contents}<TR><TD>#{v}</TD></TR>"
    }
    @contents = "#{@contents}</TABLE></TD></TR>"
  end

  def add_button(button, is_default=false)
    @contents = "#{@contents}<TR><TD></TD><TD BORDER=\"" +
                (is_default ? "2" : "1") +
                "\" BGCOLOR=\"GRAY80\">#{button}</TD></TR>"
  end

  def add_subtable(label, data, can_edit=false)
    @contents = "#{@contents}<TR><TD>#{label}</TD><TD><TABLE BORDER=\"0\""
    if can_edit then
      @contents = "#{@contents} CELLBORDER=\"1\" BGCOLOR=\"GRAY80\""
    end
    @contents = "#{@contents}>"
    data.each {|r|
      @contents = "#{@contents}<TR>"
      r.each {|c|
        @contents = "#{@contents}<TD>#{c}</TD>"
      }
      @contents = "#{@contents}</TR>"
    }
   @contents = "#{@contents}</TABLE></TD></TR>"
  end

  def to_s
    result = "<TABLE BGCOLOR=\"YELLOW\" BORDER=\"1\" CELLSPACING=\"5\" CELLBORDER=\"0\">" +
	     "<TR><TD><B>" + @title + "</B><BR ALIGN=\"LEFT\"/></TD></TR>" +
             @contents +
             "</TABLE>"
    return result
  end
end

class Link 
  def initialize(text)
    @text = text
  end

  def to_s
    return "<I>#{@text}</I>"
  end
end

class Bold
  def initialize(text)
    @text = text
  end
  
  def to_s
    return "<B>#{@text}</B>"
  end
end

# Create a new graph
g = PageLayout.new()
welcome = g.add_page( 
  "welcome",
  "/slat",
  "Welcome Page",
  'In a cloud deployment, you would need to log in before getting here.',
  Mock_Page.new("Welcome to WebSLAT") {|m|
    m.add_line("Choose an existing project:")
    m.add_list([Link.new("Redbook Example"), 
                Link.new("Project #1"),
                Link.new("Project #2")])
    m.add_line("Or")
    m.add_button("Create a new project")
  })

project_editor = g.add_page(
  "project_editor",
  '/slat/project/id#',
  'Project Editor', 
  'This is the main page for the Redbook Example Project.',
  Mock_Page.new("Redbook Example") {|m|
    m.add_text_box("Title", "Redbook Project")
    m.add_text_box("Description", "This project is based on the Redbook reference project")
    m.add_space()
    m.add_button("Submit Changes", true)
    m.add_button("Seismic Hazard")
    m.add_button("Engineering Demands")
    m.add_button("Component Library")
    m.add_button("Component Groups")
    m.add_button("Calculations")
  })


new_project = g.add_page(
  "new_project",
  '/slat/project',
  'New Project', 
  NIL,
  Mock_Page.new("Create a Project") {|m| 
    m.add_text_box("Title", "<I>Enter the project's title</I>")
    m.add_text_box("Description", "<I>Describe the project</I>")
    m.add_space()
    m.add_button("Create")
    m.add_button("Cancel", true)
  })

save = g.add_action("save", "Save the Project To the Database", 20)

hazard_editor = g.add_page_ref("hazard_editor", "Hazard Editor")
edp_editor = g.add_page_ref("edp_editor", "EDP  Editor")
component_library = g.add_page_ref("Component_library", "Component Library")
component_groups = g.add_page_ref("Component_groups", "Component Groups")
calculations = g.add_page_ref("calculations_", "Calculations")

g.connect( welcome, project_editor, "Existing Project")
g.connect( welcome, new_project, "Create a New Project")
g.connect( new_project, welcome, "Cancel")
g.connect( new_project, save, "Create")
g.connect( save, project_editor )
g.connect( project_editor, save, "Submit Changes")
g.connect( project_editor, hazard_editor, "Seismic Hazard")
g.connect( hazard_editor, project_editor, "done")
g.connect( project_editor, edp_editor, "Demand Parameters")
g.connect( edp_editor, project_editor, "done")
g.connect( project_editor, component_library, "Components")
g.connect( component_library, project_editor, "done")
g.connect( project_editor, component_groups, "Component Groups")
g.connect( component_groups, project_editor, "done")
g.connect( project_editor, calculations, "Calculations")
g.connect( calculations, project_editor, "done")

# Generate output image
#puts g.output( :none => String )
g.output( :png => "pages-test.png")
#g.output( :pdf => "pages-test.pdf")


g = PageLayout.new()
g.add_bubble("NZ Standard Curve Viewer", FALSE, :cornflowerblue)
hazard_type = g.add_page(
  "hazard_type",
  "/slat/project/#/hazard/choose",
  "Hazard Type",
  NIL,
  Mock_Page.new("Hazard Type") {|m|
    m.add_choices("Choose the hazard type",
                  ["Non-Linear Hyperbolic",
                   "User-defined Hazard Curve",
                   "NZ Standard"])
    m.add_space()
    m.add_button("Commit", true)
    m.add_button("Cancel")
  })

user_def = g.add_page(
  "user_def",
  "/slat/project/#/hazard/interp",
  "Seismic Hazard: User-defined Hazard Curve",
  "Possibly include a plot, or an option to plot.",
  Mock_Page.new("Seismic hazard") {|m|
    m.add_text_box("Type:", "User-defined Hazard Curve")
    m.add_choices("Interpolation Method:", ["Log-log", "Linear"])
    m.add_subtable("Points",
                   [[Bold.new("IM"), Bold.new("Rate")],
                    ["0.01", "0.376775"],
                    ["0.02", "0.155188"],
                    ["0.04", "0.054048"],
                    ["...", "..."]])
    m.add_space()
    m.add_button("Edit")
    m.add_button("Change Hazard Type")
    m.add_line(Link.new("Return to Project"))
  })

nzs = g.add_page(
  "nzs",
  "/slat/project/#/hazard/nzs",
  "Seismic Hazard: NZ Standard Curve",
  "Possibly include a plot, or an option to plot",
  Mock_Page.new("Seismic Hazard") {|m|
    m.add_text_box("Type:", "NZ Standard Curve")
    m.add_subtable("Parameters:",
                   [[Bold.new("Location"), "Christchurch"],
                    [Bold.new("Soil Class"), "C"],
                    [Bold.new("Period"), "1.5"]])
    m.add_space()
    m.add_button("Edit")
    m.add_button("Change Hazard Type")
    m.add_line(Link.new("Return to Project"))
  })

nlh = g.add_page(
  "nlh",
  "/slat/project/#/hazard/nlh",
  "Seismic Hazard: Non-Linear Hyperbolic",
  "Possibly include a plot, or an option to plot",
  Mock_Page.new("Seismic Hazard") {|m|
    m.add_text_box("Type:", "Non-Linear Hyperbolic")
    m.add_subtable("Parameters:",
                   [[Bold.new("V<SUB>asy</SUB>"), 1221],
                    [Bold.new("IM<SUB>asy</SUB>"), 29.8],
                    [Bold.new("alpha<SUB>asy</SUB>"), 62.2]])
    m.add_space()
    m.add_button("Edit")
    m.add_button("Change Hazard Type")
    m.add_line(Link.new("Return to Project"))
  })

user_def_edit = g.add_page(
  "user_def_edit",
  "/slat/project/#/hazard/interp/edit",
  "Hazard Point Editor",
  "There will be extra cells at the end of the list; " +
  "more can be added by commiting the form (for now; " +
  "should be a button to to this)." +
  "For now, points can be deleted by setting them " +
  "to 0,0, but there should be a button for this " +
  "as well.",
  Mock_Page.new("Hazard Point Editor") {|m|
    m.add_choices("Interpolation Method:", ["Log-log", "Linear"])
    m.add_subtable("Parameters:",
                   [[Bold.new("V<SUB>asy</SUB>"), 1221],
                    [Bold.new("IM<SUB>asy</SUB>"), 29.8],
                    [Bold.new("alpha<SUB>asy</SUB>"), 62.2]], true)
    m.add_button("Import")
    m.add_button("Commit")
    m.add_button("Cancel")
  })

user_def_import = g.add_page(
  "user_def_import",
  "/slat/project/#/hazard/interp/import",
  "Hazard Point Import",
  "Import points from a file, for interpolation",
  Mock_Page.new("Hazard Point Import") {|m|
    m.add_choices("Interpolation Method:", ["Log-log", "Linear"])
    m.add_choices("File Format:", ["Original SLAT", "CSV"])
    m.add_text_box("Path:", "<I>path/to/imfunc.csv</I>")
    m.add_space()
    m.add_button("Browse")
    m.add_button("Import")
    m.add_button("Cancel")
  })

nzs_edit = g.add_page(
  "nzs_edit",
  "/slat/project/#/hazard/nzs/edit",
  "Seismic Hazard: NZ Standard Curve",
  "Possibly inlcude a plot, or an option to plot",
  Mock_Page.new("Seisimic Hazard") {|m|
    m.add_text_box("Type:", "NZ Standard Curve")
    m.add_subtable("Parameters:",
                   [[Bold.new("Location"), "Christchurch"],
                    [Bold.new("Soil Class"), "C"],
                    [Bold.new("Period"), "1.5"]], true)
    m.add_space()
    m.add_button("Commit")
    m.add_button("Cancel")
  })

nlh_edit = g.add_page(
  "nlh_edit",
  "/slat/project/#/hazard/nlh",
  "Non-Linear Hyperbolic Editor",
  "Possibly include a plot, or an option to plot",
  Mock_Page.new("Seismic Hazard") {|m|
    m.add_text_box("Type:", "Non-Linear Hyperbolic")
    m.add_subtable("Parameters:",
                   [[Bold.new("V<SUB>asy</SUB>"), 1221],
                    [Bold.new("IM<SUB>asy</SUB>"), 29.8],
                    [Bold.new("alpha<SUB>asy</SUB>"), 62.2]], true)
    m.add_space()
    m.add_button("Edit")
    m.add_button("Change Hazard Type")
    m.add_line(Link.new("Return to Project"))
  })


puts(g.output( :none => String))
g.output( :png => "pages-test2.png")
g.output( :pdf => "pages-test2.pdf")
