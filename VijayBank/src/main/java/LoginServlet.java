

import java.io.IOException;
import java.io.PrintWriter;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

import javax.servlet.RequestDispatcher;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;


@WebServlet("/LoginServlet")
public class LoginServlet extends HttpServlet {
	private static final long serialVersionUID = 1L;
       
    
    public LoginServlet() {
        super();
        // TODO Auto-generated constructor stub
    }

	
	
	protected void doPost(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
		
       PrintWriter pw=response.getWriter();
		
		String username=request.getParameter("username");
		String password=request.getParameter("password");
		 Connection  con=null;
		try
		{
			Class.forName("oracle.jdbc.driver.OracleDriver");
			String url="jdbc:oracle:thin:@localhost:1521:xe";
			con=DriverManager.getConnection(url,"system","056679");
			
			String query = "select * from Login where username=? and password=?";
			
			PreparedStatement ps=con.prepareStatement(query);
	
			
			ps.setString(1, username);
			ps.setString(2, password);
			
			
			ResultSet rs=ps.executeQuery();
			
			if(rs.next())
			{
				pw.println("<h1> Hello"+username +", Welcome to VijayBank Services");
				
				HttpSession session=request.getSession();
				session.setAttribute("password", password);
				
				response.setContentType("text/html");
				RequestDispatcher rd=request.getRequestDispatcher("Service.html");
				rd.include(request, response);
				
			}
			else
			{
				
				pw.println("Failed to Login, Please Try Again");
				response.setContentType("text/html");
				RequestDispatcher rd=request.getRequestDispatcher("Login.html");
				rd.include(request, response);
			}
		}
		catch(Exception e)
		{
			e.getMessage();
		}
		finally
		{
			if(con != null)
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
