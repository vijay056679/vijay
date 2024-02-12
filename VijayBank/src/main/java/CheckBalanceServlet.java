

import java.io.IOException;
import java.io.PrintWriter;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

@WebServlet("/CheckBalanceServlet")
public class CheckBalanceServlet extends HttpServlet {
	private static final long serialVersionUID = 1L;
       
    
    public CheckBalanceServlet() {
        super();
      
    }

	
	protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException 
	{
		int accountnumber=Integer.parseInt(request.getParameter("accountnumber"));
		
		PrintWriter pw=response.getWriter();
		 Connection con=null;
		 try
		 {
			 Class.forName("oracle.jdbc.driver.OracleDriver");
				String url="jdbc:oracle:thin:@localhost:1521:xe";
				 con=DriverManager.getConnection(url,"system","056679");
				 String sql="select * from Account where accountnumber=?";
				 PreparedStatement ps= con.prepareStatement(sql);
				 ps.setInt(1, accountnumber);
				 
				 ResultSet rs=ps.executeQuery();
				 if(rs.next())
				 {
					 pw.println("<html>");
					 pw.println("<body Style='background-color:brown'>");
					 pw.println("<center>");
					 pw.print("<from action='CheckBalanceServlet' method='post'>");
					 pw.println("AccountNumber:");
					 pw.println(" <input type='text' value='"+rs.getInt(1)+"' + name='accountnumber'/>");
					 pw.println("<br><br>");
					 pw.println("Name:");
					 pw.println(" <input type='text' value='"+rs.getString(2)+"' + name='name'/>");
					 pw.println("<br><br>");
					 pw.println("<h2>Balance:</h2>");
					 pw.println(" <h2><input type='text' value='"+rs.getInt(3)+"' + name='balance'/></h2>");
					 pw.println("<br><br>");
					
					 pw.println(" </from>");
					 pw.println("</center>");
					 pw.println("</body>");
					 pw.println("</html>");
				 }
				 else
				 {
					 pw.println("Error: Invalid Account Number");
				 }
				
		 }
		 catch(Exception e)
		 {
			 pw.println("Excetion:"+e.getMessage());
		 }
		 finally
		 {
			 if(con !=null)
			 {
				 try {
					con.close();
				} catch (SQLException e) {
					
					e.printStackTrace();
				}
			 }
		 }
		
		
		
		
	}

	
	

}
